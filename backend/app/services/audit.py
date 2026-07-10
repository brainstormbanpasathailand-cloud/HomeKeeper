"""Audit logging helper."""
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.misc import AuditLog


def log_action(
    db: Session,
    action: str,
    actor_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str | int] = None,
    detail: Optional[dict] = None,
    request: Optional[Request] = None,
) -> AuditLog:
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        detail=detail,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(entry)
    return entry
