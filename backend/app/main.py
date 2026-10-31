from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.errors import register_exception_handlers

app = FastAPI(title="Organizational Brain API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register standardized error response handlers
register_exception_handlers(app)


@app.get("/health")
def health_check():
    return {"status": "ok"}


# Mount versioned API routes
app.include_router(api_router, prefix="/api/v1")
