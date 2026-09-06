"""
Welfare scheme routes — eligibility checks and application guidance.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
import structlog

from backend.auth.dependencies import require_worker, get_current_user
from backend.database.models import User
from backend.services.orchestrate_client import send_to_coordinator

router = APIRouter()
log = structlog.get_logger()


class WelfareQuerySchema(BaseModel):
    query: str
    language: str = "en"
    scheme_name: Optional[str] = None


@router.post("/check", summary="Check welfare scheme eligibility")
async def check_eligibility(
    body: WelfareQuerySchema,
    current_user: User = Depends(require_worker),
):
    """Routes welfare eligibility request to Welfare Scheme Agent via Main Coordinator."""
    worker_id = current_user.worker_profile.worker_id if current_user.worker_profile else None
    message = f"[WELFARE_ELIGIBILITY] {body.query}"
    if body.scheme_name:
        message = f"[WELFARE_ELIGIBILITY] Check eligibility for scheme: {body.scheme_name}. {body.query}"

    return await send_to_coordinator(
        message=message,
        user_id=str(current_user.id),
        role=current_user.role.value,
        worker_id=worker_id,
        language=body.language,
    )


@router.post("/guidance", summary="Get welfare application guidance")
async def get_guidance(
    body: WelfareQuerySchema,
    current_user: User = Depends(require_worker),
):
    """Routes welfare guidance request to Welfare Scheme Agent."""
    worker_id = current_user.worker_profile.worker_id if current_user.worker_profile else None
    message = f"[WELFARE_GUIDANCE] {body.query}"

    return await send_to_coordinator(
        message=message,
        user_id=str(current_user.id),
        role=current_user.role.value,
        worker_id=worker_id,
        language=body.language,
    )
