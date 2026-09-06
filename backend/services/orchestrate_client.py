"""
watsonx Orchestrate client — sends messages to the Main Coordinator agent.
Falls back to local knowledge base guidance when Orchestrate is not configured.
"""
import httpx
import structlog
from typing import Optional
from backend.utils.config import settings

log = structlog.get_logger()

COORDINATOR_AGENT_NAME = "migrant_welfare_coordinator"

_FALLBACK_DRAFT_MSG = (
    "The AI assistant is not yet connected to IBM watsonx Orchestrate. "
    "To enable the AI assistant, configure WXO_API_KEY and WXO_URL in your .env file. "
    "\n\nIn the meantime, you can:\n"
    "• Use the Welfare tab → Search Knowledge Base to find verified government scheme information\n"
    "• File complaints directly via the Complaint tab\n"
    "• Check your wage and profile using the Wage Check and Profile tabs\n"
    "\nKey helplines: Police: 100 | Ambulance: 108 | Labour Helpline: 1800-11-2244 | "
    "Childline: 1098 | Women: 181"
)

_WELFARE_FALLBACK = (
    "The AI assistant is not connected to IBM watsonx Orchestrate yet. "
    "Please use the 'Search Knowledge Base' feature below to find verified government information "
    "about welfare schemes (e-Shram, BOCW, PMSBY, etc.).\n\n"
    "Key schemes for migrant workers:\n"
    "• e-Shram Portal — register at eshram.gov.in (free, get UAN card + insurance)\n"
    "• PM Suraksha Bima Yojana — accident insurance ₹20/year\n"
    "• BOCW Welfare Board — for construction workers in Gujarat\n"
    "• Ayushman Bharat — health insurance\n\n"
    "To apply, visit the official government portal or nearest Labour Office."
)

_WAGE_FALLBACK = (
    "The AI assistant is not connected to IBM watsonx Orchestrate yet. "
    "Wage fairness check requires the AI agent to be configured.\n\n"
    "What you can do now:\n"
    "• Check Gujarat minimum wages at: https://labour.gujarat.gov.in/minimum-wages\n"
    "• Check national minimum wage reference at: https://labour.gov.in/wagecell.php\n"
    "• If you are being paid below minimum wage, file a complaint with your local Labour Inspector\n"
    "• Call the National Labour Helpline: 1800-11-2244 (toll-free)"
)


def _is_wxo_configured() -> bool:
    """Returns True if watsonx Orchestrate is configured with real credentials."""
    return bool(
        settings.WXO_API_KEY
        and settings.WXO_URL
        and settings.WXO_API_KEY not in ("your_ibm_cloud_api_key_here", "", "your_production_api_key")
        and settings.WXO_URL not in ("", "your_wxo_url_here")
    )


def _get_fallback_response(message: str) -> str:
    """Return a contextual fallback response based on message content."""
    msg_lower = message.lower()
    if "welfare" in msg_lower or "scheme" in msg_lower or "eligib" in msg_lower or "eshram" in msg_lower:
        return _WELFARE_FALLBACK
    if "wage" in msg_lower or "salary" in msg_lower or "मजदूरी" in message or "वेतन" in message:
        return _WAGE_FALLBACK
    return _FALLBACK_DRAFT_MSG


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
    Returns the agent's response. Falls back gracefully if not configured.
    """
    if not _is_wxo_configured():
        log.info("Orchestrate not configured — returning fallback response", user_id=user_id)
        return {
            "response": _get_fallback_response(message),
            "agent": "fallback",
            "error": False,
            "draft_mode": True,
        }

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
        "input": {"text": full_message},
    }
    if thread_id:
        payload["thread_id"] = thread_id

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.WXO_URL}/v1/orchestrate",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            # Handle various response formats from Orchestrate
            response_text = (
                data.get("output")
                or data.get("response")
                or data.get("message")
                or data.get("text")
                or str(data)
            )
            return {
                "response": response_text,
                "thread_id": data.get("thread_id") or data.get("conversation_id"),
                "agent": COORDINATOR_AGENT_NAME,
            }
    except httpx.HTTPStatusError as e:
        log.error("Orchestrate API error", status=e.response.status_code, detail=e.response.text[:200])
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
