# SECURITY

## Secrets management
- All secrets come from environment variables (`app/config.py`). **No secrets in
  source or Git.** `.env` is git-ignored; `backend/.env.example` documents every
  variable with placeholder values.
- On Render, secrets are set as `sync: false` env vars (dashboard-entered);
  `JWT_SECRET` is `generateValue: true`.
- OAuth client secrets exist **only** on the backend; the frontend never holds them.

## Authentication & sessions
- Passwords hashed with **bcrypt** (passlib).
- Access JWTs are short-lived (15 min); refresh tokens are opaque, **stored
  hashed (SHA-256)**, and **rotate on every use**. A stolen DB cannot resume
  sessions and a stolen refresh token is invalidated on next legitimate refresh.
- Sessions are revocable individually and globally (`/auth/logout-all`).
- Web auth uses `HttpOnly`, `Secure`, `SameSite` cookies in production
  (`COOKIE_SECURE=true`, `COOKIE_SAMESITE=none` for cross-site frontend↔API).

## OAuth
- Authorization Code Flow only; code exchanged and ID token/profile verified at
  the backend. `state` (signed, 10-min TTL) prevents CSRF; `nonce` prevents
  OIDC replay; Google `aud` and `email_verified` are checked; Facebook tokens
  are validated against our App ID via `debug_token`.
- One identity per provider account (`UNIQUE(provider, provider_user_id)`); no
  automatic account merging by name.

## Transport & CORS
- HTTPS end-to-end on Render.
- CORS is restricted to `CORS_ORIGINS` with credentials enabled.
- Frontend static site sets `X-Frame-Options: DENY`.

## Rate limiting & abuse
- Auth endpoints rate-limited per IP via slowapi (`RATE_LIMIT_AUTH`, default
  `10/minute`); returns `429` when exceeded. OTP/login attempt limits extend the
  same mechanism.

## Authorization (RBAC)
- Enforced server-side with FastAPI dependencies (`app/deps.py`): `require_admin`,
  `require_super_admin`, `require_roles`. Object-level checks ensure a customer
  only sees their own jobs/properties and a technician only their assigned jobs.

## Auditing
- `audit_logs` records login/failed-login, OAuth login, identity link/unlink,
  onboarding, job creation/assignment/status, quotation decisions, role changes,
  suspensions, and review moderation — with actor, IP, and user agent.
- `GET /admin/audit-logs` exposes them to admins for anomaly review.

## Error handling
- Unhandled exceptions return a generic envelope; internal details are only
  included when `ENV != production`.

## Input validation
- All request bodies validated by Pydantic v2 schemas; enum-like values checked
  before persistence; monetary values use `Numeric`.

## Recommended production hardening (roadmap)
- Verify LINE ID-token signatures against JWKS.
- Add PKCE for LINE where supported.
- Move rate-limit + idempotency stores to Redis for multi-instance correctness.
- Add security headers (CSP, HSTS) at the edge.
- Content scanning for uploaded media.

Report vulnerabilities privately to the maintainers; do not open public issues
for security matters.
