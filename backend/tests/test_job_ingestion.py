
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models.job import Job
from app.services import job_ingestion


def test_ingest_greenhouse_board_saves_jobs(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    fake_jobs = [
        {
            "source": "greenhouse",
            "external_id": "job-456",
            "title": "Backend Engineer",
            "company": "Example Tech",
            "location": "Kolkata, India",
            "description": "Build backend APIs.",
            "job_url": "https://example.com/jobs/job-456",
            "employment_type": None,
            "date_posted": None,
        }
    ]

    def fake_fetch(board_token):
        assert board_token == "example"
        return fake_jobs

    monkeypatch.setattr(
        job_ingestion,
        "fetch_greenhouse_jobs",
        fake_fetch,
    )

    try:
        with TestingSessionLocal() as session:
            result = job_ingestion.ingest_greenhouse_board(
                session,
                "example",
            )

            saved_job = session.scalar(
                select(Job).where(Job.external_id == "job-456")
            )
            count = session.scalar(
                select(func.count()).select_from(Job)
            )

            assert result == {
                "inserted": 1,
                "updated": 0,
                "total": 1,
            }
            assert saved_job is not None
            assert saved_job.title == "Backend Engineer"
            assert count == 1
    finally:
        engine.dispose()
