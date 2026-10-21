
from datetime import datetime, timezone

import pytest
import httpx

from app.services.lever import fetch_lever_jobs


def test_fetch_lever_jobs_maps_posting_fields(monkeypatch):
    """Verify that Lever postings are converted to our standard job format."""

    sample_postings = [
        {
            "id": "job-123",
            "text": "Python Developer",
            "company": "Demo Company",
            "categories": {
                "location": "Remote",
                "commitment": "Full-time",
            },
            "hostedUrl": "https://jobs.lever.co/demo/job-123",
            "descriptionPlain": "Build backend services.",
            "createdAt": 1760000000000,
        }
    ]

    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return sample_postings

    def mock_get(url, **kwargs):
        assert url == "https://api.lever.co/v0/postings/demo"
        assert kwargs["params"] == {"mode": "json"}
        return MockResponse()

    monkeypatch.setattr("app.services.lever.httpx.get", mock_get)

    jobs = fetch_lever_jobs("demo")

    assert len(jobs) == 1

    job = jobs[0]
    assert job["source"] == "lever"
    assert job["external_id"] == "job-123"
    assert job["title"] == "Python Developer"
    assert job["company"] == "Demo Company"
    assert job["location"] == "Remote"
    assert job["employment_type"] == "Full-time"
    assert job["job_url"] == "https://jobs.lever.co/demo/job-123"
    assert job["description"] == "Build backend services."
    assert job["date_posted"] == datetime.fromtimestamp(
        1760000000000 / 1000, tz=timezone.utc
    )
    assert "discovered_at" in job


def test_fetch_lever_jobs_skips_invalid_postings(monkeypatch):
    """Postings without an ID or title should be ignored."""

    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return [
                {"id": "job-1", "text": "Valid Job"},
                {"id": "job-2"},  # Missing title
                {"text": "Missing ID"},  # Missing ID
                "invalid posting",
            ]

    monkeypatch.setattr(
        "app.services.lever.httpx.get",
        lambda *args, **kwargs: MockResponse(),
    )

    jobs = fetch_lever_jobs("demo")

    assert len(jobs) == 1
    assert jobs[0]["external_id"] == "job-1"


def test_fetch_lever_jobs_rejects_empty_site():
    """An empty board identifier should raise ValueError."""

    with pytest.raises(ValueError, match="Lever site must not be empty"):
        fetch_lever_jobs("   ")


def test_fetch_lever_jobs_propagates_http_error(monkeypatch):
    """HTTP failures should not be silently ignored."""

    class MockResponse:
        def raise_for_status(self):
            raise httpx.HTTPStatusError(
                "Not found",
                request=httpx.Request(
                    "GET", "https://api.lever.co/v0/postings/demo"
                ),
                response=httpx.Response(
                    404,
                    request=httpx.Request(
                        "GET", "https://api.lever.co/v0/postings/demo"
                    ),
                ),
            )

    monkeypatch.setattr(
        "app.services.lever.httpx.get",
        lambda *args, **kwargs: MockResponse(),
    )

    with pytest.raises(httpx.HTTPStatusError):
        fetch_lever_jobs("demo")
