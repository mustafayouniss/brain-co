from fastapi import FastAPI

from app.api.v1 import api_router
from app.core.errors import register_exception_handlers

app = FastAPI(title="Organizational Brain API")

# Register standardized error response handlers
register_exception_handlers(app)


@app.get("/health")
def health_check():
    return {"status": "ok"}


# Mount versioned API routes
app.include_router(api_router, prefix="/api/v1")
