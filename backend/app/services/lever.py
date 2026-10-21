
from datetime import datetime, timezone

import httpx


LEVER_API_BASE_URL = "https://api.lever.co/v0/postings"


def fetch_lever_jobs(site: str) -> list[dict]:
    """Fetch public job postings from a Lever company site."""
    site = site.strip()

    if not site:
        raise ValueError("Lever site must not be empty")

    url = f"{LEVER_API_BASE_URL}/{site}"

    response = httpx.get(
        url,
        params={"mode": "json"},
        timeout=30.0,
        follow_redirects=True,
    )
    response.raise_for_status()

    postings = response.json()

    if not isinstance(postings, list):
        raise ValueError("Unexpected response from Lever API")

    jobs = []

    for posting in postings:
        if not isinstance(posting, dict):
            continue

        external_id = posting.get("id")
        title = posting.get("text")

        if not external_id or not title:
            continue

        categories = posting.get("categories") or {}
        if not isinstance(categories, dict):
            categories = {}

        company = posting.get("company") or site

        job_url = (
            posting.get("hostedUrl")
            or (posting.get("urls") or {}).get("show")
            or f"https://jobs.lever.co/{site}/{external_id}"
        )

        description = (
            posting.get("descriptionPlain")
            or posting.get("description")
            or ""
        )

        created_at = posting.get("createdAt")
        date_posted = None

        if isinstance(created_at, (int, float)):
            date_posted = datetime.fromtimestamp(
                created_at / 1000,
                tz=timezone.utc,
            )

        jobs.append(
            {
                "source": "lever",
                "external_id": str(external_id),
                "title": title,
                "company": company,
                "location": categories.get("location"),
                "description": description,
                "job_url": job_url,
                "employment_type": categories.get("commitment"),
                "date_posted": date_posted,
                "discovered_at": datetime.now(timezone.utc),
            }
        )

    return jobs
