"""Auth helpers: OAuth state signing and session/token issuance."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User, UserSession
from app.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    refresh_expiry,
)

STATE_TTL_SECONDS = 600


def sign_oauth_state(provider: str, nonce: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "provider": provider,
        "nonce": nonce,
        "iat": now,
        "exp": now + timedelta(seconds=STATE_TTL_SECONDS),
        "purpose": "oauth_state",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_oauth_state(state: str, provider: str) -> Optional[str]:
    """Return the nonce if the state is valid for this provider, else None."""
    try:
        payload = jwt.decode(state, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
    if payload.get("purpose") != "oauth_state" or payload.get("provider") != provider:
        return None
    return payload.get("nonce")


def issue_session(
    db: Session,
    user: User,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> tuple[str, str]:
    """Create a refresh session (stored hashed) and return (access, refresh)."""
    refresh = generate_refresh_token()
    session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_refresh_token(refresh),
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=refresh_expiry(),
        last_used_at=datetime.now(timezone.utc),
    )
    db.add(session)
    user.last_login_at = datetime.now(timezone.utc)
    access = create_access_token(subject=str(user.id), role=user.role)
    return access, refresh


def rotate_session(db: Session, session: UserSession, user: User) -> tuple[str, str]:
    """Rotate the refresh token on every use; the old hash is invalidated."""
    refresh = generate_refresh_token()
    session.refresh_token_hash = hash_refresh_token(refresh)
    session.last_used_at = datetime.now(timezone.utc)
    session.expires_at = refresh_expiry()
    access = create_access_token(subject=str(user.id), role=user.role)
    return access, refresh
