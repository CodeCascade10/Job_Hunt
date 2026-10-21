
from app.db.session import Base
from app.models.candidate import Candidate


def test_candidate_table_is_registered():
    assert "candidates" in Base.metadata.tables


def test_candidate_columns_exist():
    columns = Candidate.__table__.columns

    assert "id" in columns
    assert "full_name" in columns
    assert "email" in columns
    assert "target_role" in columns
