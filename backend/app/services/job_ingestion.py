
from sqlalchemy.orm import Session

from app.services.greenhouse import fetch_greenhouse_jobs
from app.services.job_persistence import save_jobs


def ingest_greenhouse_board(
    session: Session,
    board_token: str,
) -> dict[str, int]:
    """Fetch jobs from a Greenhouse board and persist them."""

    jobs = fetch_greenhouse_jobs(board_token)

    return save_jobs(session, jobs)
