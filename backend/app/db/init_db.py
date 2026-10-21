
from app.db.session import Base, engine
from app.models.candidate import Candidate  # noqa: F401
from app.models.job import Job


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully.")
