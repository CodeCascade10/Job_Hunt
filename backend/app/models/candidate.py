

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON, String

from app.db.session import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    target_role: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    skills: Mapped[list[str]] = mapped_column(
    JSON,
    default=list,
    nullable=False,
)
