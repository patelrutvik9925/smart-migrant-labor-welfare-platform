from backend.api.routes.auth import router as auth_router
from backend.api.routes.worker import router as worker_router
from backend.api.routes.welfare import router as welfare_router
from backend.api.routes.wage import router as wage_router
from backend.api.routes.grievance import router as grievance_router
from backend.api.routes.dashboard import router as dashboard_router
from backend.api.routes.knowledge import router as knowledge_router
from backend.api.routes.agent import router as agent_router

__all__ = [
    "auth_router", "worker_router", "welfare_router", "wage_router",
    "grievance_router", "dashboard_router", "knowledge_router", "agent_router",
]
