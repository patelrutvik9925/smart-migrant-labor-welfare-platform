"""
Knowledge base routes — admin-facing knowledge management and agent query interface.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
import structlog

from backend.database.connection import get_db
from backend.database.models import KnowledgeRecord, KnowledgeCategory, KnowledgeStatus
from backend.auth.dependencies import require_admin, get_current_user

router = APIRouter()
log = structlog.get_logger()


class KnowledgeQuerySchema(BaseModel):
    query: str
    category: Optional[str] = None  # welfare / wage / safety
    limit: int = 5


@router.get("/status", summary="Knowledge base health and current versions")
async def knowledge_status(
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Returns count of live knowledge records per category."""
    from sqlalchemy import func
    result = await db.execute(
        select(KnowledgeRecord.category, func.count(KnowledgeRecord.id))
        .where(KnowledgeRecord.status == KnowledgeStatus.LIVE, KnowledgeRecord.is_current == True)
        .group_by(KnowledgeRecord.category)
    )
    rows = result.all()
    return {
        "categories": {row[0].value: row[1] for row in rows},
        "status": "ok",
    }


@router.get("/categories", summary="List available knowledge categories")
async def list_categories():
    return {"categories": [c.value for c in KnowledgeCategory]}


@router.post("/search", summary="Search knowledge base records (authenticated)")
async def search_knowledge(
    body: KnowledgeQuerySchema,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Simple keyword search across knowledge records.
    Returns matching records with their content and structured data.
    Used by the frontend and can supplement agent responses.
    """
    stmt = (
        select(KnowledgeRecord)
        .where(
            KnowledgeRecord.status == KnowledgeStatus.LIVE,
            KnowledgeRecord.is_current == True,
        )
    )

    if body.category:
        try:
            cat = KnowledgeCategory(body.category.lower())
            stmt = stmt.where(KnowledgeRecord.category == cat)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown category: {body.category}. Valid: welfare, wage, safety")

    result = await db.execute(stmt.order_by(KnowledgeRecord.created_at.desc()).limit(50))
    records = result.scalars().all()

    # Simple keyword relevance filter
    query_lower = body.query.lower()
    query_words = set(query_lower.split())
    scored = []
    for r in records:
        text = f"{r.title} {r.content}".lower()
        tags = " ".join(r.tags or []).lower()
        combined = text + " " + tags
        score = sum(1 for w in query_words if w in combined)
        if score > 0:
            scored.append((score, r))

    # Sort by relevance
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[: body.limit]

    return {
        "query": body.query,
        "results": [
            {
                "id": str(r.id),
                "category": r.category.value,
                "title": r.title,
                "content": r.content[:500] + "..." if len(r.content) > 500 else r.content,
                "source_name": r.source_name,
                "source_url": r.source_url,
                "tags": r.tags or [],
                "structured_data": r.structured_data,
            }
            for _, r in top
        ],
        "total_found": len(top),
    }


@router.get("/records", summary="List all live knowledge records (admin only)")
async def list_knowledge_records(
    category: Optional[str] = None,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Returns all current live knowledge records for admin review."""
    stmt = select(KnowledgeRecord).where(
        KnowledgeRecord.status == KnowledgeStatus.LIVE,
        KnowledgeRecord.is_current == True,
    )
    if category:
        try:
            cat = KnowledgeCategory(category.lower())
            stmt = stmt.where(KnowledgeRecord.category == cat)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown category: {category}")

    result = await db.execute(stmt.order_by(KnowledgeRecord.category, KnowledgeRecord.title))
    records = result.scalars().all()
    return {
        "records": [
            {
                "id": str(r.id),
                "category": r.category.value,
                "title": r.title,
                "version_number": r.version_number,
                "source_name": r.source_name,
                "source_url": r.source_url,
                "tags": r.tags or [],
                "valid_from": r.valid_from.isoformat() if r.valid_from else None,
            }
            for r in records
        ],
        "total": len(records),
    }
