
import httpx
import pytest

from app.services.greenhouse import fetch_greenhouse_jobs


def test_fetch_greenhouse_jobs_normalizes_response(monkeypatch):
    def fake_get(url, **kwargs):
        assert url.endswith("/example/jobs")
        assert kwargs["params"] == {"content": "true"}

        return httpx.Response(
            200,
            json={
                "jobs": [
                    {
                        "id": 123,
                        "title": "Python Developer",
                        "company_name": "Example Company",
                        "absolute_url": (
                            "https://boards.greenhouse.io/example/jobs/123"
                        ),
                        "location": {"name": "Kolkata, India"},
                        "content": "&lt;p&gt;Python role&lt;/p&gt;",
                        "updated_at": "2026-10-20T10:00:00Z",
                    }
                ]
            },
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    jobs = fetch_greenhouse_jobs("example")

    assert len(jobs) == 1
    assert jobs[0]["source"] == "greenhouse"
    assert jobs[0]["external_id"] == "123"
    assert jobs[0]["title"] == "Python Developer"
    assert jobs[0]["company"] == "Example Company"
    assert jobs[0]["location"] == "Kolkata, India"
    assert jobs[0]["description"] == "<p>Python role</p>"
    assert jobs[0]["date_posted"] is not None
    assert jobs[0]["discovered_at"] is not None


def test_empty_board_token_is_rejected():
    with pytest.raises(ValueError, match="board token cannot be empty"):
        fetch_greenhouse_jobs("   ")


def test_http_errors_are_propagated(monkeypatch):
    def fake_get(url, **kwargs):
        return httpx.Response(
            404,
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(httpx.HTTPStatusError):
        fetch_greenhouse_jobs("example")
