"""Social login routes (LINE / Google / Facebook).

Flow:
  GET  /auth/oauth/{provider}/start     -> returns backend-built authorization URL + state
  POST /auth/oauth/{provider}/callback  -> exchanges code at backend, verifies with provider,
                                           finds/links/creates the HomeKeeper user, issues tokens
"""
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models.enums import UserRole
from app.models.user import AuthIdentity, User
from app.schemas.auth import OAuthCallbackRequest, OAuthStartResponse, TokenPair
from app.schemas.common import Message
from app.services.audit import log_action
from app.services.auth import issue_session, sign_oauth_state, verify_oauth_state
from app.services import oauth as oauth_service
from app.api.routes.auth import _set_auth_cookies

router = APIRouter(prefix="/auth/oauth", tags=["oauth"])

SUPPORTED = {"line", "google", "facebook"}


def _check_provider(provider: str) -> None:
    if provider not in SUPPORTED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown provider")


@router.get("/{provider}/start", response_model=OAuthStartResponse)
def start(provider: str):
    _check_provider(provider)
    nonce = secrets.token_urlsafe(16)
    state = sign_oauth_state(provider, nonce)
    try:
        url = oauth_service.build_authorization_url(provider, state, nonce)
    except oauth_service.OAuthError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    return OAuthStartResponse(authorization_url=url, state=state)


def _upsert_user_from_profile(db: Session, profile: oauth_service.NormalizedProfile) -> tuple[User, bool]:
    """Return (user, linked_existing_by_email)."""
    identity = (
        db.query(AuthIdentity)
        .filter(
            AuthIdentity.provider == profile.provider,
            AuthIdentity.provider_user_id == profile.provider_user_id,
        )
        .first()
    )
    if identity:
        return db.get(User, identity.user_id), False

    # No identity yet. Never auto-merge on name; only surface email matches
    # (still creating a fresh linkage, but flag that an account may exist).
    linked_existing = False
    user = None
    if profile.email:
        user = db.query(User).filter(User.email == profile.email).first()
        linked_existing = user is not None

    if not user:
        user = User(
            email=profile.email,
            email_verified=profile.email_verified,
            full_name=profile.name,
            display_name=profile.name,
            avatar_url=profile.avatar,
            role=UserRole.customer.value,
        )
        db.add(user)
        db.flush()

    db.add(
        AuthIdentity(
            user_id=user.id,
            provider=profile.provider,
            provider_user_id=profile.provider_user_id,
            provider_email=profile.email,
            provider_display_name=profile.name,
            provider_avatar_url=profile.avatar,
        )
    )
    return user, linked_existing


@router.post("/{provider}/callback", response_model=TokenPair)
def callback(
    provider: str, payload: OAuthCallbackRequest, request: Request, response: Response, db: Session = Depends(get_db)
):
    _check_provider(provider)
    nonce = verify_oauth_state(payload.state, provider)
    if nonce is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired state")
    try:
        profile = oauth_service.exchange_and_verify(provider, payload.code, expected_nonce=nonce)
    except oauth_service.OAuthError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Exception:  # provider network / parse failures
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Provider verification failed")

    user, linked_existing = _upsert_user_from_profile(db, profile)
    access, refresh = issue_session(
        db, user, request.headers.get("user-agent"), request.client.host if request.client else None
    )
    log_action(
        db,
        "user.oauth_login",
        actor_id=user.id,
        detail={"provider": provider, "linked_existing_email": linked_existing},
        request=request,
    )
    db.commit()
    _set_auth_cookies(response, access, refresh)
    return TokenPair(access_token=access, refresh_token=refresh, expires_in=settings.JWT_ACCESS_EXPIRE_MINUTES * 60)


@router.post("/{provider}/link", response_model=Message)
def link_provider(
    provider: str,
    payload: OAuthCallbackRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Link an additional provider to the currently authenticated account."""
    _check_provider(provider)
    nonce = verify_oauth_state(payload.state, provider)
    if nonce is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired state")
    try:
        profile = oauth_service.exchange_and_verify(provider, payload.code, expected_nonce=nonce)
    except oauth_service.OAuthError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))

    existing = (
        db.query(AuthIdentity)
        .filter(AuthIdentity.provider == provider, AuthIdentity.provider_user_id == profile.provider_user_id)
        .first()
    )
    if existing:
        if existing.user_id != user.id:
            raise HTTPException(status.HTTP_409_CONFLICT, "This provider is already linked to another account")
        return Message(message="Already linked")

    db.add(
        AuthIdentity(
            user_id=user.id,
            provider=provider,
            provider_user_id=profile.provider_user_id,
            provider_email=profile.email,
            provider_display_name=profile.name,
            provider_avatar_url=profile.avatar,
        )
    )
    log_action(db, "user.link_identity", actor_id=user.id, detail={"provider": provider}, request=request)
    db.commit()
    return Message(message="Provider linked")
