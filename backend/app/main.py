
from fastapi import FastAPI

from app.api.routes.health import router as health_router

from app.api.routes.ingestion import router as ingestion_router


from app.api.routes.candidates import router as candidates_router

from app.api.routes.jobs import router as jobs_router

from app.config import settings
from app.api.routes.applications import router as applications_router

from app.api.routes.resumes import router as resumes_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Backend API for the Agentic Job Hunter platform.",
)
app.include_router(health_router)

app.include_router(ingestion_router)

app.include_router(jobs_router)

app.include_router(candidates_router)
app.include_router(applications_router)

app.include_router(resumes_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Agentic Job Hunter API is running",
        "environment": settings.environment,
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
