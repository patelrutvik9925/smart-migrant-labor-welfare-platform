"""
watsonx Orchestrate client.

Exchanges the IBM Cloud API key for a temporary IAM access token
and calls the migrant welfare coordinator agent using the current
chat-completions API.
"""

import time
from typing import Optional

import httpx
import structlog

from backend.utils.config import settings

log = structlog.get_logger()

COORDINATOR_AGENT_NAME = "migrant_welfare_coordinator"
COORDINATOR_AGENT_ID = "93083d3e-626f-442f-932a-e787d12fbd71"

_cached_token: Optional[str] = None
_token_expires_at: float = 0


def _is_wxo_configured() -> bool:
    return bool(
        settings.WXO_API_KEY
        and settings.WXO_URL
        and settings.WXO_API_KEY not in (
            "",
            "your_ibm_cloud_api_key_here",
            "your_production_api_key",
        )
        and settings.WXO_URL not in (
            "",
            "your_wxo_url_here",
        )
    )


async def _get_iam_token() -> str:
    """Get and cache an IBM IAM access token."""

    global _cached_token, _token_expires_at

    now = time.time()

    # Reuse token until 60 seconds before expiry.
    if _cached_token and now < (_token_expires_at - 60):
        return _cached_token

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://iam.cloud.ibm.com/identity/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": settings.WXO_API_KEY,
            },
        )

        response.raise_for_status()
        data = response.json()

    _cached_token = data["access_token"]

    expires_in = int(data.get("expires_in", 3600))
    _token_expires_at = now + expires_in

    log.info(
        "IAM access token refreshed",
        expires_in=expires_in,
    )

    return _cached_token


async def send_to_coordinator(
    message: str,
    user_id: str,
    role: str,
    language: str = "en",
    worker_id: Optional[str] = None,
    thread_id: Optional[str] = None,
) -> dict:
    """
    Send a message to the Main Coordinator agent.
    """

    if not _is_wxo_configured():
        return {
            "response": (
                "The AI assistant is not configured yet. "
                "Please use the verified Knowledge Base."
            ),
            "agent": "fallback",
            "error": False,
            "draft_mode": True,
        }

    system_context = (
        f"User role: {role}. "
        f"User ID: {user_id}. "
        f"Preferred language: {language}. "
    )

    if worker_id:
        system_context += f"Worker ID: {worker_id}. "

    full_message = f"[CONTEXT: {system_context}] {message}"

    try:
        iam_token = await _get_iam_token()

        headers = {
            "Authorization": f"Bearer {iam_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": full_message,
                }
            ],
            "stream": False,
        }

        if thread_id:
            payload["thread_id"] = thread_id

        url = (
            f"{settings.WXO_URL.rstrip('/')}"
            f"/v1/orchestrate/{COORDINATOR_AGENT_ID}"
            f"/chat/completions"
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
            )

            response.raise_for_status()
            data = response.json()

        response_text = ""

        choices = data.get("choices") or []

        if choices:
            message_data = choices[0].get("message") or {}

            content = message_data.get("content")

            if isinstance(content, str):
                response_text = content

            elif isinstance(content, list):
                parts = []

                for item in content:
                    if isinstance(item, dict) and item.get("text"):
                        parts.append(item["text"])

                response_text = "\n".join(parts)

        if not response_text:
            response_text = (
                data.get("output")
                or data.get("response")
                or data.get("message")
                or data.get("text")
                or str(data)
            )

        return {
            "response": response_text,
            "thread_id": (
                data.get("thread_id")
                or data.get("conversation_id")
            ),
            "agent": COORDINATOR_AGENT_NAME,
            "error": False,
        }

    except httpx.HTTPStatusError as exc:
        log.error(
            "Orchestrate API error",
            status=exc.response.status_code,
            detail=exc.response.text[:300],
        )

        return {
            "response": (
                "The AI assistant is temporarily unavailable. "
                "Please try again shortly."
            ),
            "error": True,
            "agent": COORDINATOR_AGENT_NAME,
        }

    except Exception as exc:
        log.error(
            "Orchestrate connection error",
            error=str(exc),
        )

        return {
            "response": (
                "Unable to connect to the AI assistant. "
                "Please try again."
            ),
            "error": True,
            "agent": COORDINATOR_AGENT_NAME,
        }