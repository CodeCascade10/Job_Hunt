
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.job_ingestion import ingest_greenhouse_board

from app.services.lever import fetch_lever_jobs
from app.services.job_persistence import save_jobs

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/greenhouse/{board_token}")
def ingest_greenhouse(
    board_token: str,
    db: Session = Depends(get_db),
):
    try:
        return ingest_greenhouse_board(db, board_token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Greenhouse ingestion failed. Check the server logs.",
        ) from exc


@router.post("/lever/{site}")
def ingest_lever_jobs(site: str):
    with SessionLocal() as session:
        jobs = fetch_lever_jobs(site)
        result = save_jobs(session, jobs)

    return result