"""
Smart Migrant Labor Welfare & Skill Mapping Platform
Version 1 — FastAPI Backend Entry Point
"""
import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.routes import (
    auth_router,
    worker_router,
    welfare_router,
    wage_router,
    grievance_router,
    dashboard_router,
    knowledge_router,
    agent_router,
)
from backend.database.connection import init_db, close_db, get_db
from backend.utils.config import settings
from backend.audit.logger import setup_logging


setup_logging()
log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    log.info("Starting Migrant Welfare Platform backend", version="1.0.0", env=settings.ENVIRONMENT)
    await init_db()
    yield
    await close_db()
    log.info("Backend shutdown complete")


app = FastAPI(
    title="Smart Migrant Labor Welfare & Skill Mapping Platform",
    description="AI-powered platform for interstate migrant worker welfare in Gujarat",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url=None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(worker_router, prefix="/api/worker", tags=["Worker Profile"])
app.include_router(welfare_router, prefix="/api/welfare", tags=["Welfare Schemes"])
app.include_router(wage_router, prefix="/api/wage", tags=["Wage Fairness"])
app.include_router(grievance_router, prefix="/api/grievance", tags=["Grievance"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(knowledge_router, prefix="/api/knowledge", tags=["Knowledge"])
app.include_router(agent_router, prefix="/api/agent", tags=["Agent"])


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "platform": "Smart Migrant Labor Welfare & Skill Mapping Platform",
    }


@app.get("/api/health/full")
async def full_health_check(db: AsyncSession = Depends(get_db)):
    """Full health check — verifies database, storage, and Orchestrate connectivity."""
    from backend.storage.cos_client import verify_storage_connectivity
    from sqlalchemy import text

    results = {"version": "1.0.0", "environment": settings.ENVIRONMENT}

    # Database
    try:
        await db.execute(text("SELECT 1"))
        results["database"] = {"status": "ok"}
    except Exception as e:
        results["database"] = {"status": "error", "error": str(e)}

    # Storage
    results["storage"] = await verify_storage_connectivity()

    # Orchestrate
    wxo_configured = bool(settings.WXO_API_KEY and settings.WXO_API_KEY not in ("your_ibm_cloud_api_key_here", ""))
    results["orchestrate"] = {
        "status": "configured" if wxo_configured else "not_configured",
        "environment": settings.WXO_ENVIRONMENT,
        "url": settings.WXO_URL[:50] + "..." if settings.WXO_URL else "",
    }

    all_ok = all(
        v.get("status") in ("ok", "configured")
        for k, v in results.items()
        if isinstance(v, dict) and "status" in v
    )
    results["overall"] = "ok" if all_ok else "degraded"
    return results
