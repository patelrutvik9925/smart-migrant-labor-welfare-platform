"""
Safety & Grievance routes — complaint submission, evidence upload, status tracking.
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from backend.database.connection import get_db
from backend.database.models import User, Complaint, ComplaintEvidence, ComplaintStatusHistory, ComplaintPriority, ComplaintStatus
from backend.auth.dependencies import get_current_user
from backend.storage.cos_client import upload_complaint_evidence
from backend.audit.logger import audit_action
from backend.notifications.inapp import notify_admin_serious_complaint

router = APIRouter()
log = structlog.get_logger()


class ComplaintSchema(BaseModel):
    complaint_type: str
    description: str
    location_state: Optional[str] = None
    location_city: Optional[str] = None
    employer_name: Optional[str] = None
    is_anonymous: bool = False
    language: str = "en"


@router.post("/submit", summary="Submit a grievance complaint")
async def submit_complaint(
    body: ComplaintSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    worker_profile_id = None
    if not body.is_anonymous and current_user.worker_profile:
        worker_profile_id = current_user.worker_profile.id

    # Generate complaint number
    complaint_number = f"GR{str(uuid.uuid4()).replace('-','').upper()[:12]}"

    # Auto-prioritize based on type keywords
    priority = ComplaintPriority.MEDIUM
    serious_keywords = ["assault", "abuse", "trafficking", "child labor", "death", "injury", "forced"]
    if any(kw in body.description.lower() for kw in serious_keywords):
        priority = ComplaintPriority.CRITICAL

    complaint = Complaint(
        complaint_number=complaint_number,
        worker_profile_id=worker_profile_id,
        is_anonymous=body.is_anonymous,
        complaint_type=body.complaint_type,
        description=body.description,
        location_state=body.location_state,
        location_city=body.location_city,
        employer_name=body.employer_name,
        priority=priority,
        status=ComplaintStatus.SUBMITTED,
        is_serious=(priority == ComplaintPriority.CRITICAL),
        flagged_for_review=(priority in [ComplaintPriority.HIGH, ComplaintPriority.CRITICAL]),
    )
    db.add(complaint)
    await db.flush()

    # Flag serious complaints for admin notification
    if complaint.is_serious:
        await notify_admin_serious_complaint(complaint_number, body.description[:200])

    await audit_action(db, current_user.id, "complaint_submitted", "complaint", str(complaint.id))
    log.info("Complaint submitted", number=complaint_number, priority=priority.value, anonymous=body.is_anonymous)

    return {
        "complaint_number": complaint_number,
        "status": ComplaintStatus.SUBMITTED.value,
        "priority": priority.value,
        "message": "Complaint submitted successfully",
    }


@router.post("/{complaint_number}/evidence", summary="Upload evidence for a complaint")
async def upload_evidence(
    complaint_number: str,
    evidence_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Complaint).where(Complaint.complaint_number == complaint_number))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    file_bytes = await file.read()
    import hashlib
    checksum = hashlib.sha256(file_bytes).hexdigest()

    # Upload ORIGINAL — never modified
    cos_key = await upload_complaint_evidence(
        complaint_number=complaint_number,
        filename=file.filename,
        file_bytes=file_bytes,
        content_type=file.content_type,
    )

    evidence = ComplaintEvidence(
        complaint_id=complaint.id,
        original_filename=file.filename,
        cos_object_key=cos_key,  # immutable
        file_size_bytes=len(file_bytes),
        mime_type=file.content_type,
        evidence_type=evidence_type,
        checksum_sha256=checksum,
    )
    db.add(evidence)
    await audit_action(db, current_user.id, "evidence_uploaded", "complaint_evidence", str(evidence.id))

    return {"message": "Evidence uploaded", "evidence_id": str(evidence.id)}


@router.get("/{complaint_number}/status", summary="Get complaint status")
async def get_complaint_status(
    complaint_number: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Complaint).where(Complaint.complaint_number == complaint_number))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    return {
        "complaint_number": complaint.complaint_number,
        "status": complaint.status.value,
        "priority": complaint.priority.value,
        "submitted_at": complaint.submitted_at.isoformat(),
        "last_updated_at": complaint.last_updated_at.isoformat(),
        "is_serious": complaint.is_serious,
    }
