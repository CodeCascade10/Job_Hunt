
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job



from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job


def save_jobs(
    session: Session,
    jobs: list[dict[str, Any]],
) -> dict[str, int]:
    """Insert new jobs and update existing jobs by source and external ID."""

    inserted = 0
    updated = 0

    try:
        for job_data in jobs:
            source = job_data["source"]
            external_id = str(job_data["external_id"])

            existing_job = session.scalar(
                select(Job).where(
                    Job.source == source,
                    Job.external_id == external_id,
                )
            )

            if existing_job is None:
                session.add(Job(**job_data))
                inserted += 1
            else:
                for field, value in job_data.items():
                    if field not in {"id", "discovered_at"}:
                        setattr(existing_job, field, value)

                updated += 1

        session.commit()

    except Exception:
        session.rollback()
        raise

    return {
        "inserted": inserted,
        "updated": updated,
        "total": inserted + updated,
    }
