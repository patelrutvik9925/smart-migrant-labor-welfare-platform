"""
Worker profile routes — view, create, update profile; upload documents.
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import structlog

from backend.database.connection import get_db
from backend.database.models import User, WorkerProfile, WorkerSkill, WorkerDocument, WorkerProfileHistory
from backend.auth.dependencies import get_current_user, require_worker
from backend.storage.cos_client import upload_worker_document
from backend.services.document_extraction import extract_document_info
from backend.audit.logger import audit_action

router = APIRouter()
log = structlog.get_logger()


class ProfileUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    home_state: Optional[str] = None
    home_district: Optional[str] = None
    current_state: Optional[str] = None
    current_city: Optional[str] = None
    current_address: Optional[str] = None
    occupation: Optional[str] = None
    experience_years: Optional[float] = None
    education: Optional[str] = None
    employer_name: Optional[str] = None
    employer_contact: Optional[str] = None
    current_wage: Optional[float] = None
    wage_period: Optional[str] = None
    working_hours_per_day: Optional[float] = None
    working_days_per_week: Optional[float] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None


class SkillSchema(BaseModel):
    skill_name: str
    skill_level: Optional[str] = None
    years_experience: Optional[float] = None


@router.get("/profile", summary="Get worker's own profile")
async def get_profile(
    current_user: User = Depends(require_worker),
    db: AsyncSession = Depends(get_db),
):
    profile = current_user.worker_profile
    if not profile:
        return {"has_profile": False}
    return {
        "has_profile": True,
        "worker_id": profile.worker_id,
        "full_name": profile.full_name,
        "age": profile.age,
        "gender": profile.gender,
        "home_state": profile.home_state,
        "current_state": profile.current_state,
        "current_city": profile.current_city,
        "occupation": profile.occupation,
        "experience_years": profile.experience_years,
        "education": profile.education,
        "employer_name": profile.employer_name,
        "current_wage": profile.current_wage,
        "wage_period": profile.wage_period,
        "working_hours_per_day": profile.working_hours_per_day,
        "is_complete": profile.is_complete,
        "skills": [{"skill_name": s.skill_name, "skill_level": s.skill_level, "years_experience": s.years_experience} for s in profile.skills],
    }


@router.post("/profile", summary="Create or update worker profile")
async def upsert_profile(
    body: ProfileUpdateSchema,
    current_user: User = Depends(require_worker),
    db: AsyncSession = Depends(get_db),
):
    profile = current_user.worker_profile

    if not profile:
        # Generate worker ID
        worker_id = f"WK{str(uuid.uuid4()).replace('-','').upper()[:10]}"
        profile = WorkerProfile(
            user_id=current_user.id,
            worker_id=worker_id,
            full_name=body.full_name or "",
        )
        db.add(profile)
        await db.flush()
        log.info("Worker profile created", worker_id=worker_id)
    else:
        # Track history for changed fields
        changed_fields = body.model_dump(exclude_none=True)
        for field, new_val in changed_fields.items():
            old_val = getattr(profile, field, None)
            if old_val != new_val:
                history = WorkerProfileHistory(
                    worker_profile_id=profile.id,
                    field_name=field,
                    old_value=str(old_val) if old_val is not None else None,
                    new_value=str(new_val),
                    changed_by_user_id=current_user.id,
                )
                db.add(history)

    # Apply updates
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(profile, field, value)

    await audit_action(db, current_user.id, "profile_updated", "worker_profile", str(profile.id))
    return {"message": "Profile saved", "worker_id": profile.worker_id}


@router.post("/profile/skills", summary="Add skill to worker profile")
async def add_skill(
    body: SkillSchema,
    current_user: User = Depends(require_worker),
    db: AsyncSession = Depends(get_db),
):
    profile = current_user.worker_profile
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found. Create profile first.")

    skill = WorkerSkill(
        worker_profile_id=profile.id,
        skill_name=body.skill_name,
        skill_level=body.skill_level,
        years_experience=body.years_experience,
        source="manual",
    )
    db.add(skill)
    return {"message": "Skill added"}


@router.post("/profile/documents", summary="Upload a worker document")
async def upload_document(
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_worker),
    db: AsyncSession = Depends(get_db),
):
    profile = current_user.worker_profile
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found. Create profile first.")

    file_bytes = await file.read()
    cos_key = await upload_worker_document(
        worker_id=profile.worker_id,
        filename=file.filename,
        file_bytes=file_bytes,
        content_type=file.content_type,
    )

    doc = WorkerDocument(
        worker_profile_id=profile.id,
        document_type=document_type,
        original_filename=file.filename,
        cos_object_key=cos_key,
        file_size_bytes=len(file_bytes),
        mime_type=file.content_type,
        extraction_status="pending",
    )
    db.add(doc)
    await db.flush()

    # Trigger async extraction
    extracted = await extract_document_info(file_bytes, file.content_type, document_type)
    if extracted:
        doc.extracted_data = extracted
        doc.extraction_status = "completed"

    await audit_action(db, current_user.id, "document_uploaded", "worker_document", str(doc.id))
    return {"message": "Document uploaded", "document_id": str(doc.id), "extraction_status": doc.extraction_status}


@router.put("/profile/location", summary="Update worker current location")
async def update_location(
    current_state: Optional[str] = None,
    current_city: Optional[str] = None,
    gps_latitude: Optional[float] = None,
    gps_longitude: Optional[float] = None,
    current_user: User = Depends(require_worker),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone
    profile = current_user.worker_profile
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    if current_state:
        profile.current_state = current_state
    if current_city:
        profile.current_city = current_city
    if gps_latitude is not None:
        profile.gps_latitude = gps_latitude
    if gps_longitude is not None:
        profile.gps_longitude = gps_longitude
    profile.location_updated_at = datetime.now(timezone.utc)

    await audit_action(db, current_user.id, "location_updated", "worker_profile", str(profile.id))
    return {"message": "Location updated"}
