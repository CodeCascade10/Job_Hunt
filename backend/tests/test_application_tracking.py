
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.api.routes.applications import get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestSession = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    def override_get_db():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


@pytest.fixture
def candidate_and_job(client):
    # Use the isolated test database configured by the client fixture.
    db_dependency = app.dependency_overrides[get_db]
    session_generator = db_dependency()
    session = next(session_generator)

    try:
        candidate = Candidate(
            full_name="Test Candidate",
            email="application.test@example.com",
            target_role="Backend Developer",
            skills=["Python", "FastAPI"],
        )

        job = Job(
            source="greenhouse",
            external_id="application-test-job-1",
            title="Python Developer",
            company="Example Tech",
            location="Kolkata, India",
            description="Build backend services.",
            job_url="https://example.com/jobs/application-test-job-1",
            employment_type="Full-time",
            date_posted=datetime(2026, 10, 20, tzinfo=timezone.utc),
        )

        session.add_all([candidate, job])
        session.commit()
        session.refresh(candidate)
        session.refresh(job)

        yield candidate.id, job.id
    finally:
        session.close()
        try:
            next(session_generator)
        except StopIteration:
            pass


def test_create_application(client, candidate_and_job):
    candidate_id, job_id = candidate_and_job

    response = client.post(
        "/applications/",
        json={
            "candidate_id": candidate_id,
            "job_id": job_id,
            "notes": "Review the job description",
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["candidate_id"] == candidate_id
    assert data["job_id"] == job_id
    assert data["status"] == "saved"
    assert data["notes"] == "Review the job description"
    assert data["id"] > 0


def test_duplicate_application_returns_409(client, candidate_and_job):
    candidate_id, job_id = candidate_and_job
    payload = {"candidate_id": candidate_id, "job_id": job_id}

    first = client.post("/applications/", json=payload)
    second = client.post("/applications/", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_list_candidate_applications(client, candidate_and_job):
    candidate_id, job_id = candidate_and_job

    created = client.post(
        "/applications/",
        json={"candidate_id": candidate_id, "job_id": job_id},
    )
    assert created.status_code == 201

    response = client.get(f"/applications/candidate/{candidate_id}")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["job_id"] == job_id


def test_update_application_status_and_notes(client, candidate_and_job):
    candidate_id, job_id = candidate_and_job

    created = client.post(
        "/applications/",
        json={"candidate_id": candidate_id, "job_id": job_id},
    )
    application_id = created.json()["id"]

    response = client.patch(
        f"/applications/{application_id}",
        json={
            "status": "applied",
            "notes": "Application submitted",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "applied"
    assert response.json()["notes"] == "Application submitted"
    assert response.json()["applied_at"] is not None


def test_invalid_status_is_rejected(client, candidate_and_job):
    candidate_id, job_id = candidate_and_job

    created = client.post(
        "/applications/",
        json={"candidate_id": candidate_id, "job_id": job_id},
    )
    application_id = created.json()["id"]

    response = client.patch(
        f"/applications/{application_id}",
        json={"status": "invalid-status"},
    )

    assert response.status_code == 422


def test_missing_candidate_returns_404(client):
    response = client.post(
        "/applications/",
        json={"candidate_id": 999, "job_id": 1},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Candidate not found"


def test_missing_job_returns_404(client, candidate_and_job):
    candidate_id, _ = candidate_and_job

    response = client.post(
        "/applications/",
        json={"candidate_id": candidate_id, "job_id": 999},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_delete_application(client, candidate_and_job):
    candidate_id, job_id = candidate_and_job

    created = client.post(
        "/applications/",
        json={"candidate_id": candidate_id, "job_id": job_id},
    )
    application_id = created.json()["id"]

    deleted = client.delete(f"/applications/{application_id}")
    assert deleted.status_code == 204

    listed = client.get(f"/applications/candidate/{candidate_id}")
    assert listed.status_code == 200
    assert listed.json() == []


def test_missing_application_returns_404(client):
    response = client.patch(
        "/applications/999",
        json={"status": "applied"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"
