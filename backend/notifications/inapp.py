"""
In-app notification service.
"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from backend.database.models import Notification

log = structlog.get_logger()


async def notify_admin_serious_complaint(complaint_number: str, description_preview: str):
    """
    Flag a serious complaint for admin/officer notification.
    In a full deployment this would push to connected admin sessions.
    For now, logs and stores in DB when a DB session is available.
    """
    log.warning(
        "SERIOUS COMPLAINT — admin notification required",
        complaint_number=complaint_number,
        preview=description_preview[:100],
    )


async def create_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    message: str,
    notification_type: str = "info",
):
    """Create an in-app notification for a user."""
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
    )
    db.add(notif)
    log.info("Notification created", user_id=str(user_id), title=title)
