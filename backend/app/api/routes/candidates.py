
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.candidate import Candidate
from app.models.job import Job
from app.services.job_matching import rank_jobs_for_candidate
from app.services.skill_extractor import extract_skills


router = APIRouter(prefix="/candidates", tags=["Candidates"])


def get_db():
    with SessionLocal() as session:
        yield session


class CandidateCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    target_role: str | None = Field(default=None, max_length=150)
    skills: list[str] = Field(default_factory=list)


@router.post("/", status_code=201)
def create_candidate(
    candidate_data: CandidateCreate,
    session: Session = Depends(get_db),
):
    email = str(candidate_data.email).strip().lower()

    existing_candidate = (
        session.query(Candidate)
        .filter(Candidate.email == email)
        .first()
    )

    if existing_candidate:
        raise HTTPException(
            status_code=409,
            detail="A candidate with this email already exists",
        )

    # Normalize supplied skills to the canonical names in the vocabulary.
    normalized_skills = set()

    for skill in candidate_data.skills:
        skill = skill.strip()

        if skill:
            normalized_skills.update(extract_skills(skill))

    candidate = Candidate(
        full_name=candidate_data.full_name.strip(),
        email=email,
        target_role=(
            candidate_data.target_role.strip()
            if candidate_data.target_role
            else None
        ),
        skills=sorted(normalized_skills),
    )

    session.add(candidate)
    session.commit()
    session.refresh(candidate)

    return {
        "id": candidate.id,
        "full_name": candidate.full_name,
        "email": candidate.email,
        "target_role": candidate.target_role,
        "skills": candidate.skills,
    }



@router.get("/{candidate_id}")
def get_candidate(
    candidate_id: int,
    session: Session = Depends(get_db),
):
    candidate = session.get(Candidate, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found",
        )

    return {
        "id": candidate.id,
        "full_name": candidate.full_name,
        "email": candidate.email,
        "phone": candidate.phone,
        "location": candidate.location,
        "target_role": candidate.target_role,
        "preferred_locations": candidate.preferred_locations,
        "employment_types": candidate.employment_types,
        "remote_preference": candidate.remote_preference,
        "skills": candidate.skills or [],
        "years_experience": candidate.years_experience,
        "professional_summary": candidate.professional_summary,
        "education": candidate.education,
        "experience": candidate.experience,
        "projects": candidate.projects,
        "certifications": candidate.certifications,
        "resume_filename": candidate.resume_filename,
    }


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
        "candidate_skills": candidate.skills or [],
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



class CandidateSkillsUpdate(BaseModel):
    skills: list[str]



class CandidateProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    location: str | None = Field(default=None, max_length=200)
    target_role: str | None = Field(default=None, max_length=150)

    preferred_locations: list[str] | None = None
    employment_types: list[str] | None = None
    remote_preference: str | None = Field(default=None, max_length=30)

    skills: list[str] | None = None
    years_experience: float | None = Field(default=None, ge=0, le=80)
    professional_summary: str | None = None
    education: list[dict] | None = None
    experience: list[dict] | None = None
    projects: list[dict] | None = None
    certifications: list[str] | None = None



@router.patch("/{candidate_id}/skills")
def update_candidate_skills(
    candidate_id: int,
    payload: CandidateSkillsUpdate,
    session: Session = Depends(get_db),
):
    candidate = session.get(Candidate, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found",
        )

    candidate.skills = payload.skills
    session.commit()
    session.refresh(candidate)

    return {
        "id": candidate.id,
        "target_role": candidate.target_role,
        "skills": candidate.skills,
    }



@router.patch("/{candidate_id}/profile")
def update_candidate_profile(
    candidate_id: int,
    payload: CandidateProfileUpdate,
    session: Session = Depends(get_db),
):
    candidate = session.get(Candidate, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found",
        )

    updates = payload.model_dump(exclude_unset=True)

    if "email" in updates and updates["email"] is not None:
        updates["email"] = str(updates["email"]).strip().lower()

        existing = (
            session.query(Candidate)
            .filter(
                Candidate.email == updates["email"],
                Candidate.id != candidate_id,
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="A candidate with this email already exists",
            )

    if "full_name" in updates and updates["full_name"] is not None:
        updates["full_name"] = updates["full_name"].strip()

    if "skills" in updates and updates["skills"] is not None:
        normalized_skills = set()

        for skill in updates["skills"]:
            normalized_skills.update(extract_skills(skill.strip()))

        updates["skills"] = sorted(normalized_skills)

    for field, value in updates.items():
        setattr(candidate, field, value)

    try:
        session.commit()
        session.refresh(candidate)
    except Exception:
        session.rollback()
        raise

    return {
        "id": candidate.id,
        "full_name": candidate.full_name,
        "email": candidate.email,
        "phone": candidate.phone,
        "location": candidate.location,
        "target_role": candidate.target_role,
        "preferred_locations": candidate.preferred_locations,
        "employment_types": candidate.employment_types,
        "remote_preference": candidate.remote_preference,
        "skills": candidate.skills,
        "years_experience": candidate.years_experience,
        "professional_summary": candidate.professional_summary,
        "education": candidate.education,
        "experience": candidate.experience,
        "projects": candidate.projects,
        "certifications": candidate.certifications,
        "resume_filename": candidate.resume_filename,
    }
