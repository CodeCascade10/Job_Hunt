
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.job import Job


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.candidate import Candidate
from app.models.job import Job
from app.services.job_matching import (
    calculate_match_details,
    rank_jobs_for_candidate,
)


router = APIRouter(prefix="/jobs", tags=["Jobs"])


def get_db():
    with SessionLocal() as session:
        yield session


@router.get("/")
def search_jobs(
    keyword: str | None = Query(default=None, min_length=1),
    location: str | None = Query(default=None, min_length=1),
    source: str | None = Query(default=None, min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_db),
):
    query = session.query(Job)

    if keyword:
        search_term = f"%{keyword.strip()}%"
        query = query.filter(
            Job.title.ilike(search_term)
            | Job.company.ilike(search_term)
            | Job.description.ilike(search_term)
        )

    if location:
        query = query.filter(Job.location.ilike(f"%{location.strip()}%"))

    if source:
        query = query.filter(Job.source.ilike(source.strip()))

    jobs = (
        query.order_by(Job.discovered_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "count": len(jobs),
        "jobs": [
            {
                "id": job.id,
                "source": job.source,
                "external_id": job.external_id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "description": job.description,
                "job_url": job.job_url,
                "employment_type": job.employment_type,
                "date_posted": job.date_posted,
                "discovered_at": job.discovered_at,
            }
            for job in jobs
        ],
    }



@router.get("/recommendations/{candidate_id}")
def recommend_jobs(
    candidate_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_db),
):
    candidate = session.get(Candidate, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found",
        )

    jobs = session.query(Job).all()
    ranked = rank_jobs_for_candidate(candidate, jobs)

    recommendations = []

    for item in ranked:
        job = item["job"]
        details = calculate_match_details(candidate, job)

        # Do not recommend jobs with no positive match score.
        if details["match_score"] <= 0:
            continue

        recommendations.append(
            {
                "id": job.id,
                "source": job.source,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "job_url": job.job_url,
                "employment_type": job.employment_type,
                "date_posted": job.date_posted,
                "match_score": details["match_score"],
                "role_score": details["role_score"],
                "skill_score": details["skill_score"],
                "matching_skills": details["matching_skills"],
                "missing_skills": details["missing_skills"],
                "explanation": details["explanation"],
            }
        )

        if len(recommendations) >= limit:
            break

    return {
        "candidate_id": candidate.id,
        "count": len(recommendations),
        "recommendations": recommendations,
    }

