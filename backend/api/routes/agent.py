"""
Agent communication route — proxies requests to watsonx Orchestrate Main Coordinator.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import structlog

from backend.auth.dependencies import get_current_user
from backend.database.models import User
from backend.services.orchestrate_client import send_to_coordinator

router = APIRouter()
log = structlog.get_logger()


class AgentRequestSchema(BaseModel):
    message: str
    language: str = "en"  # en / hi / gu
    context: Optional[dict] = None
    thread_id: Optional[str] = None


@router.post("/chat", summary="Send message to Main Coordinator agent")
async def chat_with_coordinator(
    body: AgentRequestSchema,
    current_user: User = Depends(get_current_user),
):
    """
    Routes worker/admin/officer messages to the Main Coordinator agent.
    The coordinator determines which specialized agent handles the request.
    """
    worker_id = None
    if current_user.worker_profile:
        worker_id = current_user.worker_profile.worker_id

    response = await send_to_coordinator(
        message=body.message,
        user_id=str(current_user.id),
        role=current_user.role.value,
        worker_id=worker_id,
        language=body.language,
        thread_id=body.thread_id,
    )
    return response
