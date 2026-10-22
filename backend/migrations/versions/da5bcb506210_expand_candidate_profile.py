
"""Expand candidate profile and repair missing applications table."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "da5bcb506210"
down_revision: Union[str, Sequence[str], None] = "076dbc966c27"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existing_columns(table: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table)}



def upgrade() -> None:
    columns = [
        ("phone", sa.String(30), True),
        ("location", sa.String(200), True),
        ("preferred_locations", sa.JSON(), False),
        ("employment_types", sa.JSON(), False),
        ("remote_preference", sa.String(30), True),
        ("years_experience", sa.Float(), True),
        ("professional_summary", sa.Text(), True),
        ("education", sa.JSON(), False),
        ("experience", sa.JSON(), False),
        ("projects", sa.JSON(), False),
        ("certifications", sa.JSON(), False),
        ("resume_filename", sa.String(255), True),
    ]

    for name, column_type, nullable in columns:
        existing = _existing_columns("candidates")

        if name in existing:
            continue

        kwargs = {"nullable": nullable}

        if not nullable:
            kwargs["server_default"] = sa.text("'[]'")

        op.add_column(
            "candidates",
            sa.Column(name, column_type, **kwargs),
        )

    inspector = sa.inspect(op.get_bind())

    if "applications" not in inspector.get_table_names():
        op.create_table(
            "applications",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("candidate_id", sa.Integer(), nullable=False),
            sa.Column("job_id", sa.Integer(), nullable=False),
            sa.Column(
                "status",
                sa.String(30),
                nullable=False,
                server_default="saved",
            ),
            sa.Column("applied_at", sa.DateTime(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.current_timestamp(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.current_timestamp(),
            ),
            sa.ForeignKeyConstraint(
                ["candidate_id"],
                ["candidates.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["job_id"],
                ["jobs.id"],
                ondelete="CASCADE",
            ),
            sa.UniqueConstraint(
                "candidate_id",
                "job_id",
                name="uq_applications_candidate_job",
            ),
        )


def downgrade() -> None:
    # Intentionally leave the schema in place to avoid deleting existing
    # profile data or removing a table that may have existed before repair.
    pass
