
from app.db.session import Base, engine


def test_database_engine_is_configured():
    assert engine is not None


def test_base_metadata_exists():
    assert Base.metadata is not None
