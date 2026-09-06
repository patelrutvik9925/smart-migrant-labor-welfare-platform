"""
Database models — Version 1
All tables for worker profiles, skills, locations, welfare, wages,
complaints, notifications, audit, and knowledge versioning.
"""
import uuid
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Float, Boolean, Text, DateTime, Date,
    ForeignKey, Enum, JSON, UniqueConstraint, Index, TypeDecorator
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB as PG_JSONB
from sqlalchemy import types
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from backend.database.connection import Base


# ─── Portable column types (PostgreSQL ↔ SQLite) ─────────────────────────────

class _PortableUUID(types.TypeDecorator):
    """UUID stored as VARCHAR(36) in SQLite, native UUID in PostgreSQL."""
    impl = types.String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(types.String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        import uuid as _uuid
        if isinstance(value, _uuid.UUID):
            return value
        try:
            return _uuid.UUID(str(value))
        except Exception:
            return value


class _PortableJSON(types.TypeDecorator):
    """JSONB in PostgreSQL, JSON TEXT in SQLite."""
    impl = types.Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_JSONB())
        return dialect.type_descriptor(types.Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value
        import json
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value
        import json
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        return value


# Use these everywhere instead of UUID / JSONB directly
UUID = _PortableUUID
JSONB = _PortableJSON


# ─── Enums ─────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    WORKER = "worker"
    ADMIN = "admin"
    OFFICER = "officer"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class ComplaintPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplaintStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


class WageClassification(str, enum.Enum):
    BELOW_EXPECTED = "below_expected"
    FAIR = "fair"
    ABOVE_EXPECTED = "above_expected"


class KnowledgeCategory(str, enum.Enum):
    WELFARE = "welfare"
    WAGE = "wage"
    SAFETY = "safety"


class KnowledgeStatus(str, enum.Enum):
    DRAFT = "draft"
    TESTING = "testing"
    PENDING_REVIEW = "pending_review"
    LIVE = "live"
    ARCHIVED = "archived"
    DISABLED = "disabled"


class Language(str, enum.Enum):
    ENGLISH = "en"
    HINDI = "hi"
    GUJARATI = "gu"


# ─── Users / Auth ────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mobile_number: Mapped[str] = mapped_column(String(15), unique=True, nullable=False, index=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.WORKER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    preferred_language: Mapped[Language] = mapped_column(Enum(Language), default=Language.ENGLISH)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    worker_profile: Mapped[Optional["WorkerProfile"]] = relationship("WorkerProfile", back_populates="user", uselist=False)
    otp_records: Mapped[List["OTPRecord"]] = relationship("OTPRecord", back_populates="user")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="user")


class OTPRecord(Base):
    __tablename__ = "otp_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    otp_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="otp_records")


# ─── Worker Profile ──────────────────────────────────────────────────────────

class WorkerProfile(Base):
    __tablename__ = "worker_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    worker_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    # Personal
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gender: Mapped[Optional[Gender]] = mapped_column(Enum(Gender), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Location
    home_state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    home_district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    current_state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    current_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    current_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    gps_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gps_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Employment
    occupation: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    experience_years: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    education: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    employer_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    employer_contact: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)

    # Wage
    current_wage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wage_period: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # daily/weekly/monthly
    working_hours_per_day: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    working_days_per_week: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Profile status
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="worker_profile")
    skills: Mapped[List["WorkerSkill"]] = relationship("WorkerSkill", back_populates="worker_profile")
    documents: Mapped[List["WorkerDocument"]] = relationship("WorkerDocument", back_populates="worker_profile")
    profile_history: Mapped[List["WorkerProfileHistory"]] = relationship("WorkerProfileHistory", back_populates="worker_profile")
    complaints: Mapped[List["Complaint"]] = relationship("Complaint", back_populates="worker_profile")
    wage_records: Mapped[List["WageRecord"]] = relationship("WageRecord", back_populates="worker_profile")
    welfare_applications: Mapped[List["WelfareApplication"]] = relationship("WelfareApplication", back_populates="worker_profile")


class WorkerProfileHistory(Base):
    """Audit history — every profile change stores the previous value."""
    __tablename__ = "worker_profile_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("worker_profiles.id"), nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    changed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    worker_profile: Mapped["WorkerProfile"] = relationship("WorkerProfile", back_populates="profile_history")


class WorkerSkill(Base):
    __tablename__ = "worker_skills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("worker_profiles.id"), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(200), nullable=False)
    skill_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # beginner/intermediate/expert
    years_experience: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="manual")  # manual/extracted
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    worker_profile: Mapped["WorkerProfile"] = relationship("WorkerProfile", back_populates="skills")


class WorkerDocument(Base):
    __tablename__ = "worker_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("worker_profiles.id"), nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)  # aadhaar/pan/marksheet/etc
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    cos_object_key: Mapped[str] = mapped_column(String(1000), nullable=False)  # Cloud Object Storage key
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    extraction_status: Mapped[str] = mapped_column(String(50), default="pending")  # pending/completed/failed
    extracted_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    extracted_data_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    worker_profile: Mapped["WorkerProfile"] = relationship("WorkerProfile", back_populates="documents")


# ─── Welfare ─────────────────────────────────────────────────────────────────

class WelfareApplication(Base):
    __tablename__ = "welfare_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("worker_profiles.id"), nullable=False)
    scheme_name: Mapped[str] = mapped_column(String(500), nullable=False)
    scheme_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    eligibility_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # eligible/ineligible/needs_verification
    guidance_provided: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_analysis: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    knowledge_records_used: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    worker_profile: Mapped["WorkerProfile"] = relationship("WorkerProfile", back_populates="welfare_applications")


# ─── Wages ────────────────────────────────────────────────────────────────────

class WageRecord(Base):
    __tablename__ = "wage_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("worker_profiles.id"), nullable=False)
    reported_wage: Mapped[float] = mapped_column(Float, nullable=False)
    wage_period: Mapped[str] = mapped_column(String(20), nullable=False)
    occupation: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    location_state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    working_hours_per_day: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    classification: Mapped[Optional[WageClassification]] = mapped_column(Enum(WageClassification), nullable=True)
    reference_wage_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reference_wage_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reference_source: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ai_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    knowledge_records_used: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    worker_profile: Mapped["WorkerProfile"] = relationship("WorkerProfile", back_populates="wage_records")


# ─── Complaints / Grievances ──────────────────────────────────────────────────

class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    worker_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("worker_profiles.id"), nullable=True)  # null = anonymous
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)

    # Content
    complaint_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location_state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    employer_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    # Priority / Status
    priority: Mapped[ComplaintPriority] = mapped_column(Enum(ComplaintPriority), default=ComplaintPriority.MEDIUM)
    status: Mapped[ComplaintStatus] = mapped_column(Enum(ComplaintStatus), default=ComplaintStatus.SUBMITTED)
    is_serious: Mapped[bool] = mapped_column(Boolean, default=False)
    flagged_for_review: Mapped[bool] = mapped_column(Boolean, default=False)

    # AI Analysis (stored separately — original evidence untouched)
    ai_analysis: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ai_analysis_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Timestamps
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    worker_profile: Mapped[Optional["WorkerProfile"]] = relationship("WorkerProfile", back_populates="complaints")
    evidence: Mapped[List["ComplaintEvidence"]] = relationship("ComplaintEvidence", back_populates="complaint")
    status_history: Mapped[List["ComplaintStatusHistory"]] = relationship("ComplaintStatusHistory", back_populates="complaint")


class ComplaintEvidence(Base):
    """Original evidence — NEVER overwritten by AI analysis."""
    __tablename__ = "complaint_evidence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("complaints.id"), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    cos_object_key: Mapped[str] = mapped_column(String(1000), nullable=False)  # immutable after upload
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)  # photo/document/other
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    checksum_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # AI analysis stored SEPARATELY — never alters original
    ai_analysis_key: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)  # separate COS object
    ai_analysis_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    complaint: Mapped["Complaint"] = relationship("Complaint", back_populates="evidence")


class ComplaintStatusHistory(Base):
    __tablename__ = "complaint_status_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("complaints.id"), nullable=False)
    old_status: Mapped[Optional[ComplaintStatus]] = mapped_column(Enum(ComplaintStatus), nullable=True)
    new_status: Mapped[ComplaintStatus] = mapped_column(Enum(ComplaintStatus), nullable=False)
    changed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    complaint: Mapped["Complaint"] = relationship("Complaint", back_populates="status_history")


# ─── Knowledge Base ───────────────────────────────────────────────────────────

class KnowledgeRecord(Base):
    __tablename__ = "knowledge_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_number: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[KnowledgeCategory] = mapped_column(Enum(KnowledgeCategory), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_hi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_gu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Source
    source_name: Mapped[str] = mapped_column(String(500), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # official_api/official_download/official_website
    source_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Versioning
    status: Mapped[KnowledgeStatus] = mapped_column(Enum(KnowledgeStatus), default=KnowledgeStatus.DRAFT, index=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    previous_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_records.id"), nullable=True)
    change_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Validity
    valid_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expected_validity_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence_level: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0.0 - 1.0

    # Metadata
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    published_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Extra structured data (eligibility criteria, wage tables, etc.)
    structured_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_knowledge_category_status_current", "category", "status", "is_current"),
    )


class KnowledgeAccessLog(Base):
    """Records which agent accessed which knowledge and when."""
    __tablename__ = "knowledge_access_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_records.id"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(200), nullable=False)
    query_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    accessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    result_relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class KnowledgeUpdateLog(Base):
    __tablename__ = "knowledge_update_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_record_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_records.id"), nullable=True)
    category: Mapped[KnowledgeCategory] = mapped_column(Enum(KnowledgeCategory), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # retrieve/verify/validate/test/publish/reject/rollback
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # success/failure/rejected/pending_review
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    performed_by: Mapped[str] = mapped_column(String(200), nullable=False)  # system/user_id
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ─── Notifications ────────────────────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)  # info/warning/alert/action_required
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_sms: Mapped[bool] = mapped_column(Boolean, default=False)
    sms_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="notifications")


# ─── Audit ────────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    old_value: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_logs_user_action", "user_id", "action"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
    )
