from fastapi import APIRouter

from app.api.v1.ai import router as ai_router
from app.api.v1.auth import router as auth_router
from app.api.v1.brain import router as brain_router
from app.api.v1.cases import router as cases_router
from app.api.v1.context import router as context_router
from app.api.v1.health import router as health_router
from app.api.v1.memory import router as memory_router
from app.api.v1.observations import router as observations_router
from app.api.v1.retrieval import router as retrieval_router
from app.api.v1.ring1 import router as ring1_router
from app.api.v1.sources import router as sources_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.users import router as users_router
from app.api.v1.ws import router as ws_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(cases_router, prefix="/cases", tags=["cases"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(sources_router, prefix="/sources", tags=["sources"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
api_router.include_router(ring1_router, prefix="/ring1", tags=["ring1"])

# Ring 1 General Brain API Contracts (Section 17)
api_router.include_router(brain_router, prefix="/brain", tags=["brain"])
api_router.include_router(observations_router, prefix="/observations", tags=["observations"])
api_router.include_router(context_router, prefix="/context", tags=["context"])
api_router.include_router(memory_router, prefix="/memory", tags=["memory"])
api_router.include_router(retrieval_router, prefix="/retrieval", tags=["retrieval"])
api_router.include_router(ws_router, prefix="/ws", tags=["ws"])

