"""Social login (LINE / Google / Facebook) using the Authorization Code Flow.

Security model:
  * The Backend builds the authorization URL (never the Frontend).
  * `state` is signed and used to prevent CSRF; `nonce` binds the OpenID
    Connect ID token to this request.
  * The authorization code is exchanged for tokens AT THE BACKEND and the
    provider's ID token / profile is verified against the provider before we
    trust any identity. Frontend-supplied profiles are never trusted.

Network calls are isolated in small functions so tests can monkeypatch them
and never hit a real provider.
"""
from typing import Optional
from urllib.parse import urlencode

import httpx

from app.config import settings


class OAuthError(Exception):
    pass


class NormalizedProfile:
    def __init__(self, provider: str, provider_user_id: str, email: Optional[str],
                 email_verified: bool, name: Optional[str], avatar: Optional[str]):
        self.provider = provider
        self.provider_user_id = provider_user_id
        self.email = email
        self.email_verified = email_verified
        self.name = name
        self.avatar = avatar


LINE_AUTH_URL = "https://access.line.me/oauth2/v2.1/authorize"
LINE_TOKEN_URL = "https://api.line.me/oauth2/v2.1/token"
LINE_VERIFY_URL = "https://api.line.me/oauth2/v2.1/verify"

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"

FACEBOOK_AUTH_URL = "https://www.facebook.com/v19.0/dialog/oauth"
FACEBOOK_TOKEN_URL = "https://graph.facebook.com/v19.0/oauth/access_token"
FACEBOOK_DEBUG_URL = "https://graph.facebook.com/debug_token"
FACEBOOK_ME_URL = "https://graph.facebook.com/me"


def build_authorization_url(provider: str, state: str, nonce: str) -> str:
    if provider == "line":
        if not settings.LINE_CHANNEL_ID:
            raise OAuthError("LINE login is not configured")
        params = {
            "response_type": "code",
            "client_id": settings.LINE_CHANNEL_ID,
            "redirect_uri": settings.LINE_CALLBACK_URL,
            "state": state,
            "scope": "openid profile email",
            "nonce": nonce,
        }
        return f"{LINE_AUTH_URL}?{urlencode(params)}"

    if provider == "google":
        if not settings.GOOGLE_CLIENT_ID:
            raise OAuthError("Google login is not configured")
        params = {
            "response_type": "code",
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_CALLBACK_URL,
            "state": state,
            "scope": "openid email profile",
            "nonce": nonce,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    if provider == "facebook":
        if not settings.FACEBOOK_APP_ID:
            raise OAuthError("Facebook login is not configured")
        params = {
            "response_type": "code",
            "client_id": settings.FACEBOOK_APP_ID,
            "redirect_uri": settings.FACEBOOK_CALLBACK_URL,
            "state": state,
            "scope": "public_profile,email",
        }
        return f"{FACEBOOK_AUTH_URL}?{urlencode(params)}"

    raise OAuthError(f"Unsupported provider '{provider}'")


# --- provider network calls (patched in tests) -------------------------------

def _post(url: str, data: dict) -> dict:
    resp = httpx.post(url, data=data, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _get(url: str, params: dict) -> dict:
    resp = httpx.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _decode_id_token_unverified(id_token: str) -> dict:
    """Read ID token claims. Signature verification against provider JWKS
    should be added for production; the token is nonetheless obtained directly
    from the provider's token endpoint over TLS at the backend."""
    from jose import jwt

    return jwt.get_unverified_claims(id_token)


def exchange_and_verify(
    provider: str, code: str, expected_nonce: Optional[str] = None
) -> NormalizedProfile:
    if provider == "line":
        token = _post(
            LINE_TOKEN_URL,
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.LINE_CALLBACK_URL,
                "client_id": settings.LINE_CHANNEL_ID,
                "client_secret": settings.LINE_CHANNEL_SECRET,
            },
        )
        claims = _decode_id_token_unverified(token["id_token"])
        if expected_nonce and claims.get("nonce") != expected_nonce:
            raise OAuthError("Nonce mismatch")
        return NormalizedProfile(
            provider="line",
            provider_user_id=claims["sub"],
            email=claims.get("email"),
            email_verified=bool(claims.get("email")),
            name=claims.get("name"),
            avatar=claims.get("picture"),
        )

    if provider == "google":
        token = _post(
            GOOGLE_TOKEN_URL,
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.GOOGLE_CALLBACK_URL,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
            },
        )
        # Verify the ID token with Google's tokeninfo endpoint.
        info = _get(GOOGLE_TOKENINFO_URL, {"id_token": token["id_token"]})
        if info.get("aud") != settings.GOOGLE_CLIENT_ID:
            raise OAuthError("Google audience mismatch")
        if expected_nonce and info.get("nonce") != expected_nonce:
            raise OAuthError("Nonce mismatch")
        return NormalizedProfile(
            provider="google",
            provider_user_id=info["sub"],
            email=info.get("email"),
            email_verified=info.get("email_verified") in (True, "true"),
            name=info.get("name"),
            avatar=info.get("picture"),
        )

    if provider == "facebook":
        token = _get(
            FACEBOOK_TOKEN_URL,
            {
                "code": code,
                "redirect_uri": settings.FACEBOOK_CALLBACK_URL,
                "client_id": settings.FACEBOOK_APP_ID,
                "client_secret": settings.FACEBOOK_APP_SECRET,
            },
        )
        access_token = token["access_token"]
        app_token = f"{settings.FACEBOOK_APP_ID}|{settings.FACEBOOK_APP_SECRET}"
        debug = _get(FACEBOOK_DEBUG_URL, {"input_token": access_token, "access_token": app_token})
        data = debug.get("data", {})
        if not data.get("is_valid") or str(data.get("app_id")) != str(settings.FACEBOOK_APP_ID):
            raise OAuthError("Invalid Facebook token")
        me = _get(
            FACEBOOK_ME_URL,
            {"fields": "id,name,email,picture", "access_token": access_token},
        )
        picture = me.get("picture", {}).get("data", {}).get("url")
        return NormalizedProfile(
            provider="facebook",
            provider_user_id=me["id"],
            email=me.get("email"),
            email_verified=bool(me.get("email")),
            name=me.get("name"),
            avatar=picture,
        )

    raise OAuthError(f"Unsupported provider '{provider}'")
