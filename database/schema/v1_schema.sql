-- ============================================================
-- Smart Migrant Labor Welfare & Skill Mapping Platform
-- Version 1 — PostgreSQL Schema
-- Run via Alembic migrations or directly in development
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- ─── Enums ────────────────────────────────────────────────

CREATE TYPE user_role AS ENUM ('worker', 'admin', 'officer');
CREATE TYPE gender_type AS ENUM ('male', 'female', 'other', 'prefer_not_to_say');
CREATE TYPE complaint_priority AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE complaint_status AS ENUM ('submitted', 'under_review', 'in_progress', 'resolved', 'closed', 'reopened');
CREATE TYPE wage_classification AS ENUM ('below_expected', 'fair', 'above_expected');
CREATE TYPE knowledge_category AS ENUM ('welfare', 'wage', 'safety');
CREATE TYPE knowledge_status AS ENUM ('draft', 'testing', 'pending_review', 'live', 'archived', 'disabled');
CREATE TYPE language_type AS ENUM ('en', 'hi', 'gu');

-- ─── Users ────────────────────────────────────────────────

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mobile_number VARCHAR(15) UNIQUE NOT NULL,
    role user_role NOT NULL DEFAULT 'worker',
    is_active BOOLEAN DEFAULT TRUE,
    preferred_language language_type DEFAULT 'en',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);
CREATE INDEX ix_users_mobile ON users(mobile_number);

CREATE TABLE otp_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    otp_hash VARCHAR(128) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Worker Profiles ──────────────────────────────────────

CREATE TABLE worker_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id),
    worker_id VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    age INTEGER,
    gender gender_type,
    date_of_birth DATE,
    home_state VARCHAR(100),
    home_district VARCHAR(100),
    current_state VARCHAR(100),
    current_city VARCHAR(100),
    current_address TEXT,
    location_updated_at TIMESTAMPTZ,
    gps_latitude FLOAT,
    gps_longitude FLOAT,
    occupation VARCHAR(200),
    experience_years FLOAT,
    education VARCHAR(200),
    employer_name VARCHAR(300),
    employer_contact VARCHAR(15),
    current_wage FLOAT,
    wage_period VARCHAR(20),
    working_hours_per_day FLOAT,
    working_days_per_week FLOAT,
    is_complete BOOLEAN DEFAULT FALSE,
    profile_confirmed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ix_worker_profiles_worker_id ON worker_profiles(worker_id);

CREATE TABLE worker_profile_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    worker_profile_id UUID NOT NULL REFERENCES worker_profiles(id),
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    changed_by_user_id UUID REFERENCES users(id)
);

CREATE TABLE worker_skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    worker_profile_id UUID NOT NULL REFERENCES worker_profiles(id),
    skill_name VARCHAR(200) NOT NULL,
    skill_level VARCHAR(50),
    years_experience FLOAT,
    source VARCHAR(50) DEFAULT 'manual',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE worker_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    worker_profile_id UUID NOT NULL REFERENCES worker_profiles(id),
    document_type VARCHAR(100) NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    cos_object_key VARCHAR(1000) NOT NULL,
    file_size_bytes INTEGER,
    mime_type VARCHAR(100),
    extraction_status VARCHAR(50) DEFAULT 'pending',
    extracted_data JSONB,
    extracted_data_confirmed BOOLEAN DEFAULT FALSE,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Welfare ──────────────────────────────────────────────

CREATE TABLE welfare_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    worker_profile_id UUID NOT NULL REFERENCES worker_profiles(id),
    scheme_name VARCHAR(500) NOT NULL,
    scheme_id VARCHAR(200),
    eligibility_status VARCHAR(50),
    guidance_provided BOOLEAN DEFAULT FALSE,
    ai_analysis JSONB,
    knowledge_records_used JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Wages ────────────────────────────────────────────────

CREATE TABLE wage_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    worker_profile_id UUID NOT NULL REFERENCES worker_profiles(id),
    reported_wage FLOAT NOT NULL,
    wage_period VARCHAR(20) NOT NULL,
    occupation VARCHAR(200),
    location_state VARCHAR(100),
    location_city VARCHAR(100),
    working_hours_per_day FLOAT,
    classification wage_classification,
    reference_wage_min FLOAT,
    reference_wage_max FLOAT,
    reference_source VARCHAR(500),
    ai_explanation TEXT,
    knowledge_records_used JSONB,
    assessed_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Complaints ────────────────────────────────────────────

CREATE TABLE complaints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    complaint_number VARCHAR(30) UNIQUE NOT NULL,
    worker_profile_id UUID REFERENCES worker_profiles(id),  -- NULL = anonymous
    is_anonymous BOOLEAN DEFAULT FALSE,
    complaint_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    location_state VARCHAR(100),
    location_city VARCHAR(100),
    employer_name VARCHAR(300),
    priority complaint_priority DEFAULT 'medium',
    status complaint_status DEFAULT 'submitted',
    is_serious BOOLEAN DEFAULT FALSE,
    flagged_for_review BOOLEAN DEFAULT FALSE,
    ai_analysis JSONB,
    ai_analysis_version VARCHAR(20),
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    last_updated_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);
CREATE INDEX ix_complaints_number ON complaints(complaint_number);
CREATE INDEX ix_complaints_serious ON complaints(is_serious, status);

CREATE TABLE complaint_evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    complaint_id UUID NOT NULL REFERENCES complaints(id),
    original_filename VARCHAR(500) NOT NULL,
    cos_object_key VARCHAR(1000) NOT NULL,  -- IMMUTABLE after upload
    file_size_bytes INTEGER,
    mime_type VARCHAR(100),
    evidence_type VARCHAR(50) NOT NULL,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    checksum_sha256 VARCHAR(64),
    ai_analysis_key VARCHAR(1000),          -- Separate COS object for AI analysis
    ai_analysis_completed_at TIMESTAMPTZ
);

CREATE TABLE complaint_status_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    complaint_id UUID NOT NULL REFERENCES complaints(id),
    old_status complaint_status,
    new_status complaint_status NOT NULL,
    changed_by_user_id UUID REFERENCES users(id),
    note TEXT,
    changed_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Knowledge Base ────────────────────────────────────────

CREATE TABLE knowledge_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version_number VARCHAR(20) NOT NULL,
    category knowledge_category NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    content_en TEXT,
    content_hi TEXT,
    content_gu TEXT,
    source_name VARCHAR(500) NOT NULL,
    source_url VARCHAR(2000),
    source_type VARCHAR(50) NOT NULL,
    source_active BOOLEAN DEFAULT TRUE,
    status knowledge_status DEFAULT 'draft',
    is_current BOOLEAN DEFAULT FALSE,
    previous_version_id UUID REFERENCES knowledge_records(id),
    change_summary TEXT,
    valid_from DATE,
    valid_until DATE,
    expected_validity_days INTEGER,
    confidence_level FLOAT,
    last_verified_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    published_by_user_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    structured_data JSONB,
    tags JSONB
);
CREATE INDEX ix_knowledge_category_status ON knowledge_records(category, status, is_current);
CREATE INDEX ix_knowledge_content_search ON knowledge_records USING gin(to_tsvector('english', content));

CREATE TABLE knowledge_access_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    knowledge_record_id UUID NOT NULL REFERENCES knowledge_records(id),
    agent_name VARCHAR(200) NOT NULL,
    query_text TEXT,
    accessed_at TIMESTAMPTZ DEFAULT NOW(),
    result_relevance_score FLOAT
);

CREATE TABLE knowledge_update_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    knowledge_record_id UUID REFERENCES knowledge_records(id),
    category knowledge_category NOT NULL,
    action VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    reason TEXT,
    source_url VARCHAR(2000),
    performed_by VARCHAR(200) NOT NULL,
    performed_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Notifications ─────────────────────────────────────────

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(500) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) NOT NULL DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    sent_sms BOOLEAN DEFAULT FALSE,
    sms_sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Audit ─────────────────────────────────────────────────

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(200) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(200),
    old_value JSONB,
    new_value JSONB,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    performed_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ix_audit_logs_user ON audit_logs(user_id, action);
CREATE INDEX ix_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX ix_audit_logs_time ON audit_logs(performed_at DESC);

-- ─── Updated timestamp trigger ─────────────────────────────

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_worker_profiles_updated_at BEFORE UPDATE ON worker_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_welfare_applications_updated_at BEFORE UPDATE ON welfare_applications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_knowledge_records_updated_at BEFORE UPDATE ON knowledge_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_complaints_updated_at BEFORE UPDATE ON complaints FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
