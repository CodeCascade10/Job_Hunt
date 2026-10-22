
from sqlalchemy import JSON, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Basic information
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Job preferences
    target_role: Mapped[str | None] = mapped_column(
        String(150), nullable=True
    )
    preferred_locations: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    employment_types: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    remote_preference: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )

    # Professional profile
    skills: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    years_experience: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    professional_summary: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    education: Mapped[list[dict]] = mapped_column(
        JSON, default=list, nullable=False
    )
    experience: Mapped[list[dict]] = mapped_column(
        JSON, default=list, nullable=False
    )
    projects: Mapped[list[dict]] = mapped_column(
        JSON, default=list, nullable=False
    )
    certifications: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )

    # Resume metadata
    resume_filename: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
