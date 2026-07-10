"""Email/password authentication, token refresh, session management."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.ratelimit import AUTH_LIMIT, limiter
from app.database import get_db
from app.deps import get_current_user
from app.models.enums import AuthProvider, NotificationType, UserRole
from app.models.user import AuthIdentity, User, UserSession
from app.schemas.auth import (
    IdentityOut,
    LoginRequest,
    OnboardingRequest,
    RefreshRequest,
    RegisterRequest,
    SessionOut,
    TokenPair,
    UserOut,
)
from app.schemas.common import Message
from app.security import hash_password, hash_refresh_token, verify_password
from app.services.audit import log_action
from app.services.auth import issue_session, rotate_session
from app.services.notifications import notify

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    common = dict(
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN or None,
    )
    response.set_cookie("access_token", access, max_age=settings.JWT_ACCESS_EXPIRE_MINUTES * 60, **common)
    response.set_cookie("refresh_token", refresh, max_age=settings.JWT_REFRESH_EXPIRE_DAYS * 86400, **common)


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
@limiter.limit(AUTH_LIMIT)
def register(request: Request, payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        display_name=payload.full_name,
        role=UserRole.customer.value,
    )
    db.add(user)
    db.flush()
    db.add(
        AuthIdentity(
            user_id=user.id,
            provider=AuthProvider.password.value,
            provider_user_id=payload.email,
            provider_email=payload.email,
        )
    )
    access, refresh = issue_session(
        db, user, request.headers.get("user-agent"), request.client.host if request.client else None
    )
    notify(db, user.id, NotificationType.account_created, "ยินดีต้อนรับสู่ HomeKeeper", "สมัครสมาชิกสำเร็จ")
    log_action(db, "user.register", actor_id=user.id, entity_type="user", entity_id=user.id, request=request)
    db.commit()
    _set_auth_cookies(response, access, refresh)
    return TokenPair(access_token=access, refresh_token=refresh, expires_in=settings.JWT_ACCESS_EXPIRE_MINUTES * 60)


@router.post("/login", response_model=TokenPair)
@limiter.limit(AUTH_LIMIT)
def login(request: Request, payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        log_action(db, "user.login_failed", entity_type="user", detail={"email": payload.email}, request=request)
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if user.is_suspended or not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account not available")
    access, refresh = issue_session(
        db, user, request.headers.get("user-agent"), request.client.host if request.client else None
    )
    log_action(db, "user.login", actor_id=user.id, entity_type="user", entity_id=user.id, request=request)
    db.commit()
    _set_auth_cookies(response, access, refresh)
    return TokenPair(access_token=access, refresh_token=refresh, expires_in=settings.JWT_ACCESS_EXPIRE_MINUTES * 60)


@router.post("/refresh", response_model=TokenPair)
def refresh_token(request: Request, response: Response, payload: RefreshRequest | None = None, db: Session = Depends(get_db)):
    raw = (payload.refresh_token if payload else None) or request.cookies.get("refresh_token")
    if not raw:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing refresh token")
    session = (
        db.query(UserSession)
        .filter(UserSession.refresh_token_hash == hash_refresh_token(raw), UserSession.revoked == False)  # noqa: E712
        .first()
    )
    expires_at = session.expires_at if session else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if not session or expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")
    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not available")
    access, new_refresh = rotate_session(db, session, user)
    db.commit()
    _set_auth_cookies(response, access, new_refresh)
    return TokenPair(access_token=access, refresh_token=new_refresh, expires_in=settings.JWT_ACCESS_EXPIRE_MINUTES * 60)


@router.post("/logout", response_model=Message)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    raw = request.cookies.get("refresh_token")
    if raw:
        session = db.query(UserSession).filter(UserSession.refresh_token_hash == hash_refresh_token(raw)).first()
        if session:
            session.revoked = True
            db.commit()
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return Message(message="Logged out")


@router.post("/logout-all", response_model=Message)
def logout_all(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(UserSession).filter(UserSession.user_id == user.id).update({"revoked": True})
    log_action(db, "user.logout_all", actor_id=user.id, request=request)
    db.commit()
    return Message(message="All sessions revoked")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/onboarding", response_model=UserOut)
def complete_onboarding(
    request: Request, payload: OnboardingRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if not payload.accept_tos or not payload.accept_privacy:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Terms of Service and Privacy Policy must be accepted")
    if payload.display_name:
        user.display_name = payload.display_name
    if payload.phone:
        user.phone = payload.phone
    if payload.province:
        user.province = payload.province
    if payload.district:
        user.district = payload.district
    if payload.subdistrict:
        user.subdistrict = payload.subdistrict
    if payload.language:
        user.language = payload.language
    user.onboarding_completed = True
    log_action(db, "user.onboarding", actor_id=user.id, request=request)
    db.commit()
    db.refresh(user)
    return user


@router.get("/identities", response_model=list[IdentityOut])
def list_identities(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(AuthIdentity).filter(AuthIdentity.user_id == user.id).all()


@router.delete("/identities/{identity_id}", response_model=Message)
def unlink_identity(
    identity_id: int, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    identity = db.get(AuthIdentity, identity_id)
    if not identity or identity.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Identity not found")
    count = db.query(AuthIdentity).filter(AuthIdentity.user_id == user.id).count()
    if count <= 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot unlink the last login method")
    db.delete(identity)
    log_action(db, "user.unlink_identity", actor_id=user.id, detail={"provider": identity.provider}, request=request)
    db.commit()
    return Message(message="Identity unlinked")


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(UserSession).filter(UserSession.user_id == user.id, UserSession.revoked == False).all()  # noqa: E712
