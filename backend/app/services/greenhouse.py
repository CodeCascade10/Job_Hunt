
from datetime import datetime, timezone
from html import unescape
from typing import Any

import httpx


GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards"


def fetch_greenhouse_jobs(
    board_token: str,
    timeout: float = 20.0,
) -> list[dict[str, Any]]:
    """Fetch published jobs from one public Greenhouse job board."""

    board_token = board_token.strip()

    if not board_token:
        raise ValueError("Greenhouse board token cannot be empty")

    url = f"{GREENHOUSE_API}/{board_token}/jobs"

    response = httpx.get(
        url,
        params={"content": "true"},
        timeout=timeout,
        follow_redirects=True,
    )
    response.raise_for_status()

    payload = response.json()
    jobs = payload.get("jobs", [])

    normalized_jobs = []

    for item in jobs:
        job_id = item.get("id")
        title = item.get("title")
        job_url = item.get("absolute_url")

        # Skip incomplete records that cannot satisfy our Job model.
        if job_id is None or not title or not job_url:
            continue

        location_data = item.get("location") or {}
        location = location_data.get("name")

        description = item.get("content")
        if description:
            description = unescape(description)

        updated_at = item.get("updated_at")
        date_posted = None

        if updated_at:
            try:
                date_posted = datetime.fromisoformat(
                    updated_at.replace("Z", "+00:00")
                )
            except ValueError:
                date_posted = None

        normalized_jobs.append(
            {
                "source": "greenhouse",
                "external_id": str(job_id),
                "title": title,
                "company": item.get("company_name") or board_token,
                "location": location,
                "description": description,
                "job_url": job_url,
                "employment_type": None,
                "date_posted": date_posted,
                "discovered_at": datetime.now(timezone.utc),
            }
        )

    return normalized_jobs
