
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.db.session import SessionLocal
from app.models.candidate import Candidate
from app.models.job import Job
from app.services.job_matching import rank_jobs_for_candidate

router = APIRouter(prefix="/candidates", tags=["Candidates"])


def get_db():
    with SessionLocal() as session:
        yield session


@router.get("/{candidate_id}/matched-jobs")
def get_matched_jobs(
    candidate_id: int,
    session: Session = Depends(get_db),
):
    candidate = (
        session.query(Candidate)
        .filter(Candidate.id == candidate_id)
        .first()
    )

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found",
        )

    jobs = session.query(Job).all()

    ranked_jobs = rank_jobs_for_candidate(candidate, jobs)

    return {
        "candidate_id": candidate.id,
        "candidate_name": candidate.full_name,
        "target_role": candidate.target_role,
        "count": len(ranked_jobs),
        "jobs": [
            {
                "job_id": item["job"].id,
                "title": item["job"].title,
                "company": item["job"].company,
                "location": item["job"].location,
                "source": item["job"].source,
                "job_url": item["job"].job_url,
                "match_score": item["match_score"],
            }
            for item in ranked_jobs
        ],
    }

class CandidateCreate(BaseModel):
    full_name: str
    email: EmailStr
    target_role: str | None = None


@router.post("/", status_code=201)
def create_candidate(
    candidate_data: CandidateCreate,
    session: Session = Depends(get_db),
):
    existing_candidate = (
        session.query(Candidate)
        .filter(Candidate.email == candidate_data.email)
        .first()
    )

    if existing_candidate:
        raise HTTPException(
            status_code=409,
            detail="A candidate with this email already exists",
        )

    candidate = Candidate(
        full_name=candidate_data.full_name,
        email=candidate_data.email,
        target_role=candidate_data.target_role,
    )

    session.add(candidate)
    session.commit()
    session.refresh(candidate)

    return {
        "id": candidate.id,
        "full_name": candidate.full_name,
        "email": candidate.email,
        "target_role": candidate.target_role,
    }