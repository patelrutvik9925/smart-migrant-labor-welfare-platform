"""
Comprehensive API endpoint tests — in-process FastAPI test client.
Tests auth, worker profile, skills, documents, welfare, wage, grievance,
dashboard, and knowledge endpoints.
"""
import asyncio
import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture(scope="module")
async def app_and_db():
    """Set up the FastAPI app with a fresh SQLite test database."""
    import tempfile
    import pathlib

    # Use a temp SQLite db for tests
    test_db = pathlib.Path(tempfile.mktemp(suffix=".db"))

    # Patch DB path for test
    import backend.database.connection as db_conn
    original_build = db_conn._build_database_url

    def _test_db_url():
        test_db.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{test_db}"

    db_conn._build_database_url = _test_db_url
    db_conn._use_local = None  # reset cache

    await db_conn.init_db()

    from backend.main import app
    yield app

    await db_conn.close_db()
    db_conn._build_database_url = original_build
    if test_db.exists():
        test_db.unlink()


@pytest.fixture(scope="module")
async def client(app_and_db):
    async with AsyncClient(transport=ASGITransport(app=app_and_db), base_url="http://test") as c:
        yield c


async def _get_token_for_mobile(client, mobile: str, role: str) -> str:
    """Helper: register mobile, retrieve OTP from DB, verify and return token."""
    from backend.api.routes.auth import _generate_otp, _hash_otp
    from backend.database import connection as db_conn
    from backend.database.models import OTPRecord, User
    from sqlalchemy import select
    from datetime import datetime, timedelta, timezone

    # Patch OTP generation to return a known value during tests
    known_otp = "123456"
    known_hash = _hash_otp(known_otp)

    # Insert user + OTP record directly into the test DB
    async with db_conn.AsyncSessionLocal() as db:
        user_result = await db.execute(select(User).where(User.mobile_number == mobile))
        user = user_result.scalar_one_or_none()
        if not user:
            from backend.database.models import UserRole
            user = User(mobile_number=mobile, role=UserRole(role))
            db.add(user)
            await db.flush()

        otp_record = OTPRecord(
            user_id=user.id,
            otp_hash=known_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        db.add(otp_record)
        await db.commit()

    r = await client.post("/api/auth/otp/verify", json={"mobile_number": mobile, "otp": known_otp})
    assert r.status_code == 200, f"OTP verify failed: {r.text}"
    data = r.json()
    assert "access_token" in data
    return data["access_token"]


@pytest.fixture(scope="module")
async def worker_token(client):
    """Register a test worker and return auth token."""
    return await _get_token_for_mobile(client, "+919876543210", "worker")


@pytest.fixture(scope="module")
async def admin_token(client):
    """Register a test admin and return auth token."""
    return await _get_token_for_mobile(client, "+919000000001", "admin")


# ── Tests ────────────────────────────────────────────────────────────────────

async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"


async def test_health_full(client):
    r = await client.get("/api/health/full")
    assert r.status_code == 200
    data = r.json()
    assert "database" in data
    assert "storage" in data
    assert data["database"]["status"] == "ok"
    assert data["storage"]["status"] == "ok"


async def test_otp_request_and_verify(client):
    """Tests OTP request for a fresh mobile number."""
    r = await client.post("/api/auth/otp/request", json={"mobile_number": "+919111111111", "role": "worker"})
    assert r.status_code == 200
    assert "expires_in_seconds" in r.json()


async def test_auth_requires_token(client):
    """Protected routes return 403 without token."""
    r = await client.get("/api/worker/profile")
    assert r.status_code == 403  # missing bearer returns 403 in FastAPI


async def test_worker_profile_create(client, worker_token):
    headers = {"Authorization": f"Bearer {worker_token}"}
    body = {
        "full_name": "Ramesh Kumar",
        "age": 28,
        "gender": "male",
        "home_state": "Rajasthan",
        "current_state": "Gujarat",
        "current_city": "Surat",
        "occupation": "Construction Worker",
        "experience_years": 5.0,
        "education": "10th Standard",
        "employer_name": "ABC Builders",
        "current_wage": 450.0,
        "wage_period": "daily",
        "working_hours_per_day": 8.0,
    }
    r = await client.post("/api/worker/profile", json=body, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "worker_id" in data
    assert data["worker_id"].startswith("WK")


async def test_worker_profile_get(client, worker_token):
    headers = {"Authorization": f"Bearer {worker_token}"}
    r = await client.get("/api/worker/profile", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["has_profile"] is True
    assert data["full_name"] == "Ramesh Kumar"
    assert data["occupation"] == "Construction Worker"


async def test_worker_add_skill(client, worker_token):
    headers = {"Authorization": f"Bearer {worker_token}"}
    r = await client.post("/api/worker/profile/skills", json={"skill_name": "Bricklaying", "skill_level": "expert"}, headers=headers)
    assert r.status_code == 200


async def test_worker_profile_skill_visible(client, worker_token):
    headers = {"Authorization": f"Bearer {worker_token}"}
    r = await client.get("/api/worker/profile", headers=headers)
    assert r.status_code == 200
    data = r.json()
    skills = [s["skill_name"] for s in data.get("skills", [])]
    assert "Bricklaying" in skills


async def test_worker_update_location(client, worker_token):
    headers = {"Authorization": f"Bearer {worker_token}"}
    r = await client.put(
        "/api/worker/profile/location",
        params={"current_state": "Gujarat", "current_city": "Ahmedabad", "gps_latitude": 23.02, "gps_longitude": 72.57},
        headers=headers
    )
    assert r.status_code == 200


async def test_grievance_submit(client, worker_token):
    headers = {"Authorization": f"Bearer {worker_token}"}
    body = {
        "complaint_type": "wage_dispute",
        "description": "My employer has not paid wages for 2 months.",
        "location_state": "Gujarat",
        "location_city": "Surat",
        "employer_name": "ABC Builders",
        "is_anonymous": False,
    }
    r = await client.post("/api/grievance/submit", json=body, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "complaint_number" in data
    assert data["complaint_number"].startswith("GR")
    assert data["status"] == "submitted"
    return data["complaint_number"]


async def test_grievance_critical_auto_priority(client, worker_token):
    """Critical keywords should auto-escalate priority."""
    headers = {"Authorization": f"Bearer {worker_token}"}
    body = {
        "complaint_type": "harassment",
        "description": "My employer is physically assaulting workers at the construction site.",
        "location_state": "Gujarat",
        "is_anonymous": True,
    }
    r = await client.post("/api/grievance/submit", json=body, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["priority"] == "critical"


async def test_grievance_status(client, worker_token):
    """Submit a complaint and check its status."""
    headers = {"Authorization": f"Bearer {worker_token}"}
    body = {
        "complaint_type": "non_payment",
        "description": "Employer withheld 3 weeks of salary.",
        "location_state": "Gujarat",
        "is_anonymous": False,
    }
    r = await client.post("/api/grievance/submit", json=body, headers=headers)
    assert r.status_code == 200
    complaint_num = r.json()["complaint_number"]

    r2 = await client.get(f"/api/grievance/{complaint_num}/status", headers=headers)
    assert r2.status_code == 200
    data = r2.json()
    assert data["complaint_number"] == complaint_num
    assert data["status"] == "submitted"


async def test_worker_dashboard(client, worker_token):
    headers = {"Authorization": f"Bearer {worker_token}"}
    r = await client.get("/api/dashboard/worker", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data.get("has_profile") is not False
    assert "worker_id" in data


async def test_admin_dashboard(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    r = await client.get("/api/dashboard/admin", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "total_workers" in data
    assert "open_complaints" in data


async def test_knowledge_categories(client):
    """Knowledge categories endpoint is public."""
    r = await client.get("/api/knowledge/categories")
    assert r.status_code == 200
    data = r.json()
    assert "categories" in data
    assert "welfare" in data["categories"]
    assert "wage" in data["categories"]
    assert "safety" in data["categories"]


async def test_agent_chat_no_orchestrate(client, worker_token):
    """Agent chat should return graceful error when Orchestrate is not configured."""
    headers = {"Authorization": f"Bearer {worker_token}"}
    r = await client.post("/api/agent/chat", json={"message": "What welfare schemes can I apply for?", "language": "en"}, headers=headers)
    assert r.status_code == 200
    data = r.json()
    # Response should always have 'response' field (even if Orchestrate is unavailable)
    assert "response" in data


async def test_welfare_check_no_orchestrate(client, worker_token):
    """Welfare check should return graceful error when Orchestrate is not configured."""
    headers = {"Authorization": f"Bearer {worker_token}"}
    r = await client.post("/api/welfare/check", json={"query": "Am I eligible for e-Shram?"}, headers=headers)
    assert r.status_code == 200
    assert "response" in r.json()


async def test_wage_check_no_orchestrate(client, worker_token):
    """Wage check should return graceful error when Orchestrate is not configured."""
    headers = {"Authorization": f"Bearer {worker_token}"}
    r = await client.post("/api/wage/check", json={
        "current_wage": 350.0,
        "wage_period": "daily",
        "occupation": "construction worker",
        "location_state": "Gujarat",
        "working_hours_per_day": 8.0,
    }, headers=headers)
    assert r.status_code == 200
    assert "response" in r.json()


async def test_knowledge_search(client, worker_token):
    """Knowledge search returns seeded records matching query."""
    headers = {"Authorization": f"Bearer {worker_token}"}

    # Seed test DB
    from backend.database import connection as db_conn
    from backend.database.models import KnowledgeRecord, KnowledgeCategory, KnowledgeStatus
    from knowledge.seeds.initial_knowledge import KNOWLEDGE_SEEDS
    from sqlalchemy import select
    import uuid
    from datetime import date

    async with db_conn.AsyncSessionLocal() as db:
        result = await db.execute(select(KnowledgeRecord).where(KnowledgeRecord.is_current == True).limit(1))
        if not result.scalar_one_or_none():
            for seed in KNOWLEDGE_SEEDS[:3]:
                record = KnowledgeRecord(
                    id=uuid.uuid4(),
                    version_number=seed["version_number"],
                    category=KnowledgeCategory(seed["category"]),
                    title=seed["title"],
                    content=seed["content"],
                    content_en=seed["content"],
                    source_name=seed["source_name"],
                    source_url=seed.get("source_url"),
                    source_type=seed["source_type"],
                    source_active=True,
                    status=KnowledgeStatus.LIVE,
                    is_current=True,
                    structured_data=seed.get("structured_data"),
                    tags=seed.get("tags", []),
                    confidence_level=0.9,
                    valid_from=date.today(),
                )
                db.add(record)
            await db.commit()

    r = await client.post("/api/knowledge/search", json={"query": "e-Shram registration", "category": "welfare", "limit": 3}, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "results" in data
    assert data["total_found"] > 0
    assert data["results"][0]["category"] == "welfare"


async def test_knowledge_search_no_category(client, worker_token):
    """Knowledge search without category filter searches all categories."""
    headers = {"Authorization": f"Bearer {worker_token}"}
    r = await client.post("/api/knowledge/search", json={"query": "helpline", "limit": 5}, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "results" in data


async def test_officer_dashboard(client, admin_token):
    """Officer dashboard returns serious cases without personal worker data."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    r = await client.get("/api/dashboard/officer", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "serious_cases" in data
    assert "note" in data
    for case in data.get("serious_cases", []):
        assert "mobile" not in case
        assert "full_name" not in case
