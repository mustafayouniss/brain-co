from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.sources import router as sources_router
from app.api.v1.users import router as users_router
from app.api.v1.ai import router as ai_router
from app.api.v1.ring1 import router as ring1_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(sources_router, prefix="/sources", tags=["sources"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
api_router.include_router(ring1_router, prefix="/ring1", tags=["ring1"])
