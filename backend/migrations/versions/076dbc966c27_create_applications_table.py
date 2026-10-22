
"""create applications table

Revision ID: 076dbc966c27
Revises: 42784e4070bf
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "076dbc966c27"
down_revision: Union[str, Sequence[str], None] = "42784e4070bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["candidate_id"], ["candidates.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["jobs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "candidate_id",
            "job_id",
            name="uq_applications_candidate_job",
        ),
    )

    op.create_index(
        "ix_applications_id", "applications", ["id"], unique=False
    )
    op.create_index(
        "ix_applications_candidate_id",
        "applications",
        ["candidate_id"],
        unique=False,
    )
    op.create_index(
        "ix_applications_job_id", "applications", ["job_id"], unique=False
    )
    op.create_index(
        "ix_applications_status", "applications", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_applications_status", table_name="applications")
    op.drop_index("ix_applications_job_id", table_name="applications")
    op.drop_index("ix_applications_candidate_id", table_name="applications")
    op.drop_index("ix_applications_id", table_name="applications")
    op.drop_table("applications")
