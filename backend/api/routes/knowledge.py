"""
Knowledge base routes — admin-facing knowledge management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import structlog

from backend.database.connection import get_db
from backend.database.models import KnowledgeRecord, KnowledgeCategory, KnowledgeStatus
from backend.auth.dependencies import require_admin

router = APIRouter()
log = structlog.get_logger()


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
