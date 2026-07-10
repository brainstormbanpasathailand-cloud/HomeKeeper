"""In-app notification creation. Designed so email / LINE / push can be added
later by extending `dispatch` without changing call sites."""
from typing import Optional

from sqlalchemy.orm import Session

from app.models.enums import NotificationType
from app.models.misc import Notification


def notify(
    db: Session,
    user_id: int,
    ntype: NotificationType,
    title: str,
    body: Optional[str] = None,
    data: Optional[dict] = None,
) -> Notification:
    n = Notification(
        user_id=user_id,
        type=ntype.value,
        title=title,
        body=body,
        data=data,
    )
    db.add(n)
    # Future channels (email, LINE Messaging API, web push) would be dispatched
    # here via background tasks. In-app record is the source of truth.
    return n
