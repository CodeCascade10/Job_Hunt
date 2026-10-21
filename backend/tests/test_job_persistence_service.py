
from datetime import datetime, timezone

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models.job import Job
from app.services.job_persistence import save_jobs


def create_test_session():
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

    return engine, TestingSessionLocal




def sample_job(**overrides):
    job = {
        "source": "greenhouse",
        "external_id": "job-123",
        "title": "Python Developer",
        "company": "Example Tech",
        "location": "Kolkata, India",
        "description": "Build backend services.",
        "job_url": "https://example.com/jobs/job-123",
        "employment_type": "Full-time",
        "date_posted": datetime(2026, 10, 20, tzinfo=timezone.utc),
        "discovered_at": datetime(2026, 10, 21, tzinfo=timezone.utc),
    }
    job.update(overrides)
    return job


def test_save_jobs_inserts_new_job():
    engine, TestingSessionLocal = create_test_session()

    try:
        with TestingSessionLocal() as session:
            result = save_jobs(session, [sample_job()])

            saved_job = session.scalar(
                select(Job).where(Job.external_id == "job-123")
            )

            assert result == {
                "inserted": 1,
                "updated": 0,
                "total": 1,
            }
            assert saved_job is not None
            assert saved_job.title == "Python Developer"
    finally:
        engine.dispose()


def test_save_jobs_updates_existing_job_without_duplicate():
    engine, TestingSessionLocal = create_test_session()

    try:
        with TestingSessionLocal() as session:
            first_discovered_at = datetime(
                2026, 10, 21, tzinfo=timezone.utc
            )

            save_jobs(
                session,
                [sample_job(discovered_at=first_discovered_at)],
            )

            result = save_jobs(
                session,
                [
                    sample_job(
                        title="Senior Python Developer",
                        discovered_at=datetime(
                            2026, 10, 22, tzinfo=timezone.utc
                        ),
                    )
                ],
            )

            count = session.scalar(
                select(func.count()).select_from(Job)
            )
            saved_job = session.scalar(
                select(Job).where(
                    Job.source == "greenhouse",
                    Job.external_id == "job-123",
                )
            )

            assert result == {
                "inserted": 0,
                "updated": 1,
                "total": 1,
            }
            assert count == 1
            assert saved_job.title == "Senior Python Developer"
            assert saved_job.discovered_at.replace(tzinfo=timezone.utc) == first_discovered_at
    finally:
        engine.dispose()


def test_same_external_id_from_different_source_is_not_duplicate():
    engine, TestingSessionLocal = create_test_session()

    try:
        with TestingSessionLocal() as session:
            first = sample_job(source="greenhouse")
            second = sample_job(
                source="lever",
                title="Backend Developer",
            )

            result = save_jobs(session, [first, second])

            count = session.scalar(
                select(func.count()).select_from(Job)
            )

            assert result == {
                "inserted": 2,
                "updated": 0,
                "total": 2,
            }
            assert count == 2
    finally:
        engine.dispose()
