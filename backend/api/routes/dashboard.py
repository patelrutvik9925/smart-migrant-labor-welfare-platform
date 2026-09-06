"""
Dashboard routes — Worker / Admin / Officer views.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import structlog

from backend.database.connection import get_db
from backend.database.models import (
    User, WorkerProfile, Complaint, ComplaintStatus, ComplaintPriority,
    WageRecord, WelfareApplication, UserRole
)
from backend.auth.dependencies import get_current_user, require_admin_or_officer, require_worker

router = APIRouter()
log = structlog.get_logger()


@router.get("/worker", summary="Worker personal dashboard")
async def worker_dashboard(
    current_user: User = Depends(require_worker),
    db: AsyncSession = Depends(get_db),
):
    profile = current_user.worker_profile
    if not profile:
        return {"has_profile": False, "message": "Please complete your profile to see your dashboard."}

    # Recent complaints (explicit query — avoids lazy load)
    complaints_result = await db.execute(
        select(Complaint)
        .where(Complaint.worker_profile_id == profile.id)
        .order_by(Complaint.submitted_at.desc())
        .limit(5)
    )
    complaints = complaints_result.scalars().all()

    # Recent wage assessments (explicit query)
    wages_result = await db.execute(
        select(WageRecord)
        .where(WageRecord.worker_profile_id == profile.id)
        .order_by(WageRecord.assessed_at.desc())
        .limit(3)
    )
    wages = wages_result.scalars().all()

    # Skills count from eagerly-loaded relationship (loaded by auth dependency)
    skills_count = len(current_user.worker_profile.skills) if current_user.worker_profile.skills is not None else 0

    return {
        "has_profile": True,
        "worker_id": profile.worker_id,
        "full_name": profile.full_name,
        "current_location": f"{profile.current_city}, {profile.current_state}" if profile.current_city else profile.current_state,
        "occupation": profile.occupation,
        "profile_complete": profile.is_complete,
        "skills_count": skills_count,
        "recent_complaints": [
            {"number": c.complaint_number, "status": c.status.value, "priority": c.priority.value}
            for c in complaints
        ],
        "recent_wage_assessments": [
            {"classification": w.classification.value if w.classification else None, "assessed_at": w.assessed_at.isoformat()}
            for w in wages
        ],
    }


@router.get("/admin", summary="Admin operational dashboard")
async def admin_dashboard(
    current_user: User = Depends(require_admin_or_officer),
    db: AsyncSession = Depends(get_db),
):
    # Total workers
    total_workers = await db.execute(select(func.count(User.id)).where(User.role == UserRole.WORKER))

    # Complaints by status
    critical_complaints = await db.execute(
        select(func.count(Complaint.id)).where(Complaint.priority == ComplaintPriority.CRITICAL, Complaint.status != ComplaintStatus.CLOSED)
    )
    open_complaints = await db.execute(
        select(func.count(Complaint.id)).where(Complaint.status.in_([ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW, ComplaintStatus.IN_PROGRESS]))
    )
    flagged_complaints = await db.execute(
        select(func.count(Complaint.id)).where(Complaint.flagged_for_review == True, Complaint.status != ComplaintStatus.CLOSED)
    )

    return {
        "total_workers": total_workers.scalar(),
        "open_complaints": open_complaints.scalar(),
        "critical_complaints": critical_complaints.scalar(),
        "flagged_for_review": flagged_complaints.scalar(),
        "role": current_user.role.value,
    }


@router.get("/officer", summary="Government/Labor Officer dashboard")
async def officer_dashboard(
    current_user: User = Depends(require_admin_or_officer),
    db: AsyncSession = Depends(get_db),
):
    """
    Officer dashboard — area-level labor monitoring.
    Personal worker data is hidden by default.
    """
    # Serious / flagged complaints — no personal worker data exposed
    serious_result = await db.execute(
        select(
            Complaint.complaint_number,
            Complaint.complaint_type,
            Complaint.priority,
            Complaint.status,
            Complaint.location_state,
            Complaint.location_city,
            Complaint.submitted_at,
        )
        .where(Complaint.is_serious == True, Complaint.status != ComplaintStatus.CLOSED)
        .order_by(Complaint.submitted_at.desc())
        .limit(20)
    )
    serious_complaints = serious_result.all()

    return {
        "serious_cases": [
            {
                "complaint_number": r.complaint_number,
                "type": r.complaint_type,
                "priority": r.priority.value,
                "status": r.status.value,
                "location": f"{r.location_city or ''}, {r.location_state or ''}".strip(", "),
                "submitted_at": r.submitted_at.isoformat(),
            }
            for r in serious_complaints
        ],
        "note": "Personal worker information is hidden by default. Request case-specific access from Admin.",
    }
