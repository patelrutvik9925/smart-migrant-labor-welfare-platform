"""
Authentication routes — Mobile OTP login.
Roles: worker / admin / officer
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from jose import jwt
import structlog

from backend.database.connection import get_db
from backend.database.models import User, OTPRecord, UserRole, WorkerProfile
from backend.utils.config import settings
from backend.audit.logger import audit_action
from backend.notifications.sms import send_otp_sms

router = APIRouter()
log = structlog.get_logger()


# ─── Schemas ─────────────────────────────────────────────────────────────────

class OTPRequestSchema(BaseModel):
    mobile_number: str
    role: str = "worker"


class OTPVerifySchema(BaseModel):
    mobile_number: str
    otp: str


class TokenResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    worker_id: str | None = None
    user_id: str


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


def _create_jwt(user_id: str, role: str, mobile: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "mobile": mobile,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def _generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return str(secrets.randbelow(900000) + 100000)


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/otp/request", summary="Request OTP for login")
async def request_otp(body: OTPRequestSchema, request: Request, db: AsyncSession = Depends(get_db)):
    """Send OTP to the provided mobile number."""
    mobile = body.mobile_number.strip()
    if not mobile.startswith("+"):
        mobile = "+91" + mobile.lstrip("0")

    # Find or create user
    result = await db.execute(select(User).where(User.mobile_number == mobile))
    user = result.scalar_one_or_none()

    if not user:
        try:
            role = UserRole(body.role)
        except ValueError:
            role = UserRole.WORKER
        user = User(mobile_number=mobile, role=role)
        db.add(user)
        await db.flush()

    # Generate and store OTP
    otp = _generate_otp()
    otp_record = OTPRecord(
        user_id=user.id,
        otp_hash=_hash_otp(otp),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.OTP_EXPIRY_SECONDS),
    )
    db.add(otp_record)

    # Send OTP via SMS
    sms_sent = await send_otp_sms(mobile, otp)
    log.info("OTP requested", mobile=mobile[-4:], sms_sent=sms_sent)

    await audit_action(db, None, "otp_requested", "user", str(user.id))

    return {"message": "OTP sent", "expires_in_seconds": settings.OTP_EXPIRY_SECONDS}


@router.post("/otp/verify", response_model=TokenResponseSchema, summary="Verify OTP and get token")
async def verify_otp(body: OTPVerifySchema, request: Request, db: AsyncSession = Depends(get_db)):
    """Verify OTP and return a JWT access token."""
    mobile = body.mobile_number.strip()
    if not mobile.startswith("+"):
        mobile = "+91" + mobile.lstrip("0")

    result = await db.execute(
        select(User)
        .options(selectinload(User.worker_profile).selectinload(WorkerProfile.skills))
        .where(User.mobile_number == mobile)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP")

    # Find valid unused OTP
    now = datetime.now(timezone.utc)
    otp_result = await db.execute(
        select(OTPRecord).where(
            OTPRecord.user_id == user.id,
            OTPRecord.used == False,
            OTPRecord.expires_at > now,
            OTPRecord.otp_hash == _hash_otp(body.otp),
        )
    )
    otp_record = otp_result.scalar_one_or_none()

    if not otp_record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OTP")

    # Mark OTP used
    otp_record.used = True
    user.last_login = now

    token = _create_jwt(str(user.id), user.role.value, mobile)

    # Get worker_id if applicable
    worker_id = None
    if user.worker_profile:
        worker_id = user.worker_profile.worker_id

    await audit_action(db, user.id, "login_success", "user", str(user.id))
    log.info("Login success", user_id=str(user.id), role=user.role.value)

    return TokenResponseSchema(
        access_token=token,
        role=user.role.value,
        worker_id=worker_id,
        user_id=str(user.id),
    )
