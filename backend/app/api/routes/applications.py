
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
)

router = APIRouter(prefix="/applications", tags=["Applications"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
):
    candidate = db.get(Candidate, payload.candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")

    job = db.get(Job, payload.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    application = Application(
        candidate_id=payload.candidate_id,
        job_id=payload.job_id,
        status="saved",
        notes=payload.notes,
    )

    db.add(application)
    try:
        db.commit()
        db.refresh(application)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This job is already saved for this candidate",
        )

    return application


@router.get(
    "/candidate/{candidate_id}",
    response_model=list[ApplicationResponse],
)
def list_candidate_applications(
    candidate_id: int,
    db: Session = Depends(get_db),
):
    if db.get(Candidate, candidate_id) is None:
        raise HTTPException(status_code=404, detail="Candidate not found")

    statement = (
        select(Application)
        .where(Application.candidate_id == candidate_id)
        .order_by(Application.created_at.desc())
    )
    return list(db.scalars(statement).all())


@router.patch(
    "/{application_id}",
    response_model=ApplicationResponse,
)
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
):
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")

    changes = payload.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(status_code=422, detail="No fields supplied")

    if "status" in changes:
        application.status = changes["status"]

        if changes["status"] == "applied" and application.applied_at is None:
            application.applied_at = datetime.now(timezone.utc)

    if "notes" in changes:
        application.notes = changes["notes"]

    db.commit()
    db.refresh(application)
    return application


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
):
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")

    db.delete(application)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
