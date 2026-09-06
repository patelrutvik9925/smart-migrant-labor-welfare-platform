"""
watsonx Orchestrate client — sends messages to the Main Coordinator agent.
"""
import httpx
import structlog
from typing import Optional
from backend.utils.config import settings

log = structlog.get_logger()

COORDINATOR_AGENT_NAME = "migrant-welfare-coordinator"


async def send_to_coordinator(
    message: str,
    user_id: str,
    role: str,
    language: str = "en",
    worker_id: Optional[str] = None,
    thread_id: Optional[str] = None,
) -> dict:
    """
    Send a message to the Main Coordinator agent via watsonx Orchestrate API.
    Returns the agent's response.
    """
    # Build context header for agent
    system_context = (
        f"User role: {role}. "
        f"User ID: {user_id}. "
        f"Preferred language: {language}. "
    )
    if worker_id:
        system_context += f"Worker ID: {worker_id}. "

    full_message = f"[CONTEXT: {system_context}] {message}"

    headers = {
        "Authorization": f"Bearer {settings.WXO_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "agent_name": COORDINATOR_AGENT_NAME,
        "message": full_message,
    }
    if thread_id:
        payload["thread_id"] = thread_id

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.WXO_URL}/v1/chat",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "response": data.get("output", data.get("message", "")),
                "thread_id": data.get("thread_id"),
                "agent": COORDINATOR_AGENT_NAME,
            }
    except httpx.HTTPStatusError as e:
        log.error("Orchestrate API error", status=e.response.status_code, detail=e.response.text)
        return {
            "response": "I'm sorry, the assistant is temporarily unavailable. Please try again shortly.",
            "error": True,
        }
    except Exception as e:
        log.error("Orchestrate connection error", error=str(e))
        return {
            "response": "Unable to connect to the assistant. Please try again.",
            "error": True,
        }
