
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base
from app.api.routes.jobs import get_db
from app.models.job import Job


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base.metadata.create_all(engine)


def override_get_db():
    with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def seed_jobs():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with TestingSessionLocal() as session:
        session.add_all(
            [
                Job(
                    source="lever",
                    external_id="lever-1",
                    title="Python Developer",
                    company="Example Tech",
                    location="Remote",
                    description="Build backend services using Python.",
                    job_url="https://example.com/lever-1",
                    employment_type="Full-time",
                    date_posted=datetime.now(timezone.utc),
                ),
                Job(
                    source="greenhouse",
                    external_id="greenhouse-1",
                    title="Java Developer",
                    company="Kolkata Systems",
                    location="Kolkata, India",
                    description="Build Java applications.",
                    job_url="https://example.com/greenhouse-1",
                    employment_type="Full-time",
                    date_posted=datetime.now(timezone.utc),
                ),
            ]
        )
        session.commit()


def test_job_search_returns_jobs():
    seed_jobs()

    response = client.get("/jobs/")

    assert response.status_code == 200
    assert response.json()["count"] == 2


def test_job_search_filters_by_keyword():
    seed_jobs()

    response = client.get("/jobs/", params={"keyword": "python"})

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["jobs"][0]["title"] == "Python Developer"


def test_job_search_filters_by_location():
    seed_jobs()

    response = client.get("/jobs/", params={"location": "remote"})

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["jobs"][0]["location"] == "Remote"


def test_job_search_filters_by_source():
    seed_jobs()

    response = client.get("/jobs/", params={"source": "lever"})

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["jobs"][0]["source"] == "lever"


def test_job_search_combines_filters():
    seed_jobs()

    response = client.get(
        "/jobs/",
        params={
            "keyword": "python",
            "location": "remote",
            "source": "lever",
        },
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_job_search_respects_limit():
    seed_jobs()

    response = client.get("/jobs/", params={"limit": 1})

    assert response.status_code == 200
    assert len(response.json()["jobs"]) == 1


def test_job_search_returns_empty_results():
    seed_jobs()

    response = client.get(
        "/jobs/",
        params={"keyword": "nonexistent-specialist-role"},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 0
    assert response.json()["jobs"] == []
