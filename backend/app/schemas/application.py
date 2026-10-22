
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ApplicationStatus = Literal[
    "saved",
    "applied",
    "interview",
    "offer",
    "rejected",
    "withdrawn",
]


class ApplicationCreate(BaseModel):
    candidate_id: int = Field(gt=0)
    job_id: int = Field(gt=0)
    notes: str | None = None


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = None
    notes: str | None = None


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    job_id: int
    status: ApplicationStatus
    applied_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
