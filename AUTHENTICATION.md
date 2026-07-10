# AUTHENTICATION

HomeKeeper supports multiple login channels that all resolve to **one**
HomeKeeper `user_id`.

Primary: **LINE Login**, **Google**, **Facebook**.
Fallback: **Email + Password** (implemented), **Phone + OTP** and **Email magic
link** (schema/flows reserved for a later phase).

## Principles

1. **Backend is the source of truth.** The frontend never sends a user profile
   or provider token that we trust blindly. We always exchange the authorization
   code and verify the ID token / profile with the provider at the backend.
2. **Authorization Code Flow** for all social providers.
3. **CSRF via `state`**, **replay protection via `nonce`** (OIDC).
4. **No client secrets in the frontend.** All secrets live in backend env vars.
5. **One account per person** — enforced by `UNIQUE(provider, provider_user_id)`
   on `auth_identities`. We never auto-merge accounts just because names match.

## JWT & Sessions

| Token | Lifetime | Storage |
|-------|----------|---------|
| Access token (JWT, HS256) | 15 min (`JWT_ACCESS_EXPIRE_MINUTES`) | memory / HttpOnly cookie |
| Refresh token (opaque, 48 bytes) | 30 days (`JWT_REFRESH_EXPIRE_DAYS`) | **hashed (SHA-256)** in `user_sessions` |

- Refresh tokens **rotate on every use** — `/auth/refresh` invalidates the old
  hash and issues a new one.
- Sessions record `user_agent`, `ip_address`, `expires_at`, `last_used_at`, and
  can be revoked individually or all at once (`/auth/logout-all`).
- Web clients receive `HttpOnly`, `Secure`, `SameSite` cookies (configurable via
  `COOKIE_SECURE` / `COOKIE_SAMESITE`).

## Social Login Flow

```
Frontend                    Backend                      Provider
   │   GET /oauth/{p}/start    │                            │
   │──────────────────────────>│  sign state+nonce (JWT)    │
   │   {authorization_url}     │  build authorize URL        │
   │<──────────────────────────│                            │
   │   redirect user ──────────────────────────────────────>│  consent
   │   /auth/callback/{p}?code&state <──────────────────────│
   │   POST /oauth/{p}/callback │                            │
   │──────────────────────────>│  verify state → nonce      │
   │                           │  exchange code ───────────>│  token endpoint
   │                           │  verify ID token / profile │ (aud, nonce, email_verified)
   │                           │  upsert user + identity     │
   │   {access, refresh}       │  issue session              │
   │<──────────────────────────│                            │
```

### Per-provider verification (`app/services/oauth.py`)

- **LINE:** OAuth 2.0 + OIDC. Scopes `openid profile email`. Exchange code at
  the backend, read the ID token, check `nonce`, store the LINE `sub` as
  `provider_user_id`. LINE access tokens are not persisted.
- **Google:** exchange code, verify the ID token via Google's `tokeninfo`
  endpoint, check `aud == GOOGLE_CLIENT_ID`, `nonce`, and `email_verified`.
  Store Google `sub`.
- **Facebook:** exchange code, `debug_token` to confirm the token is valid and
  bound to our `App ID`, then read `id,name,email,picture`. Store Facebook `id`.

> Signature verification against provider JWKS is the recommended production
> hardening step for LINE; the token is nonetheless obtained directly from the
> provider's TLS token endpoint at the backend and its `nonce`/`aud` are checked.

## Account Linking

`auth_identities` columns: `id, user_id, provider, provider_user_id,
provider_email, provider_display_name, provider_avatar_url, created_at,
updated_at, last_login_at`, with `UNIQUE(provider, provider_user_id)`.

- If an incoming identity already exists → log in that user.
- If not, and the verified email matches an existing user → we surface that a
  prior account exists (the response flags `linked_existing_email`); linking a
  new provider to an existing account is an authenticated action via
  `/auth/oauth/{provider}/link`.
- The **Security** page lets users view linked channels, link LINE/Google/
  Facebook, and unlink — but **the last remaining login method cannot be
  removed** (`DELETE /auth/identities/{id}` returns 400).

## Rate limiting & audit

- `/auth/register` and `/auth/login` are rate-limited per IP (`RATE_LIMIT_AUTH`).
- Logins, failed logins, OAuth logins, identity link/unlink, and admin actions
  are written to `audit_logs` (actor, action, ip, user_agent).

## Testing OAuth

`tests/test_oauth.py` monkeypatches `exchange_and_verify` — **no real provider
credentials or network calls** are used. It asserts: callback creates a user,
a repeat login reuses the same `user_id` (no duplicates), and a tampered `state`
is rejected.
