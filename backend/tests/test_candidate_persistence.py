
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models.candidate import Candidate


def test_candidate_can_be_saved_and_retrieved():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=test_engine)

    TestSession = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )

    with TestSession() as session:
        candidate = Candidate(
            full_name="Test Candidate",
            email="test.candidate@example.com",
            target_role="Backend Developer",
        )

        session.add(candidate)
        session.commit()
        candidate_id = candidate.id

    with TestSession() as session:
        saved_candidate = session.get(Candidate, candidate_id)

        assert saved_candidate is not None
        assert saved_candidate.full_name == "Test Candidate"
        assert saved_candidate.email == "test.candidate@example.com"
        assert saved_candidate.target_role == "Backend Developer"

    test_engine.dispose()
