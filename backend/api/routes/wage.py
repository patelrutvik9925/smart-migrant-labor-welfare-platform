"""
Wage fairness routes.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
import structlog

from backend.auth.dependencies import require_worker
from backend.database.models import User
from backend.services.orchestrate_client import send_to_coordinator

router = APIRouter()
log = structlog.get_logger()


class WageCheckSchema(BaseModel):
    current_wage: float
    wage_period: str  # daily/weekly/monthly
    occupation: str
    location_state: str
    location_city: Optional[str] = None
    working_hours_per_day: Optional[float] = None
    language: str = "en"


@router.post("/check", summary="Check wage fairness")
async def check_wage(
    body: WageCheckSchema,
    current_user: User = Depends(require_worker),
):
    worker_id = current_user.worker_profile.worker_id if current_user.worker_profile else None
    message = (
        f"[WAGE_FAIRNESS] Check if this wage is fair: "
        f"Wage={body.current_wage} {body.wage_period}, "
        f"Occupation={body.occupation}, "
        f"State={body.location_state}, City={body.location_city or 'not specified'}, "
        f"Working hours={body.working_hours_per_day or 'not specified'} per day."
    )
    return await send_to_coordinator(
        message=message,
        user_id=str(current_user.id),
        role=current_user.role.value,
        worker_id=worker_id,
        language=body.language,
    )
