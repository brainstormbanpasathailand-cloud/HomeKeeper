"""Shared FastAPI dependencies: DB session, current user, RBAC guards."""
from typing import Callable, Iterable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.security import decode_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    token = None
    if credentials:
        token = credentials.credentials
    else:
        # Fall back to HttpOnly cookie for browser clients.
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active or user.is_suspended:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not available")
    return user


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    allowed: Iterable[str] = {r.value for r in roles}

    def guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return user

    return guard


# Convenience guards
def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in {UserRole.admin.value, UserRole.super_admin.value, UserRole.dispatcher.value}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return user


def require_super_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.super_admin.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Super admin access required")
    return user
