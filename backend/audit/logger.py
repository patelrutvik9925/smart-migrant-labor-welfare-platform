"""
Audit logger — records important actions with user, resource, old/new values.
"""
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from backend.database.models import AuditLog

log = structlog.get_logger()


async def audit_action(
    db: AsyncSession,
    user_id: Optional[uuid.UUID],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
    ip_address: Optional[str] = None,
):
    """Record an auditable action to the audit_logs table."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
    )
    db.add(entry)
    log.info("Audit", action=action, resource_type=resource_type, resource_id=resource_id, user_id=str(user_id) if user_id else None)


def setup_logging():
    """Configure structlog for structured JSON logging."""
    import logging
    import sys
    import os
    from backend.utils.config import settings

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Ensure log directory exists
    os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True) if "/" in settings.LOG_FILE or "\\" in settings.LOG_FILE else None

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if settings.BACKEND_DEBUG else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
