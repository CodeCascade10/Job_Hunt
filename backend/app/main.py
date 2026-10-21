
from fastapi import FastAPI

from app.api.routes.health import router as health_router

from app.api.routes.ingestion import router as ingestion_router

from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Backend API for the Agentic Job Hunter platform.",
)
app.include_router(health_router)

app.include_router(ingestion_router)

@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Agentic Job Hunter API is running",
        "environment": settings.environment,
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
