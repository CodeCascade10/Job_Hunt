
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models.job import Job


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


def test_job_can_be_saved():
    engine, TestingSessionLocal = create_test_session()

    try:
        with TestingSessionLocal() as session:
            job = Job(
                source="greenhouse",
                external_id="job-123",
                title="Python Developer",
                company="Example Tech",
                location="Kolkata, India",
                description="Build backend services using Python.",
                job_url="https://example.com/jobs/job-123",
                employment_type="Full-time",
                date_posted=datetime.now(timezone.utc),
            )

            session.add(job)
            session.commit()

            saved_job = session.scalar(
                select(Job).where(Job.external_id == "job-123")
            )

            assert saved_job is not None
            assert saved_job.title == "Python Developer"
            assert saved_job.company == "Example Tech"
            assert saved_job.source == "greenhouse"
            assert saved_job.id is not None
            assert saved_job.discovered_at is not None
    finally:
        engine.dispose()


def test_duplicate_job_from_same_source_is_rejected():
    engine, TestingSessionLocal = create_test_session()

    try:
        with TestingSessionLocal() as session:
            job1 = Job(
                source="greenhouse",
                external_id="job-123",
                title="Python Developer",
                company="Example Tech",
                job_url="https://example.com/jobs/job-123",
            )

            job2 = Job(
                source="greenhouse",
                external_id="job-123",
                title="Backend Developer",
                company="Example Tech",
                job_url="https://example.com/jobs/job-123",
            )

            session.add(job1)
            session.commit()

            session.add(job2)

            try:
                session.commit()
                assert False, "Expected duplicate job to be rejected"
            except IntegrityError:
                session.rollback()
    finally:
        engine.dispose()
