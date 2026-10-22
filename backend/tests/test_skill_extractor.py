
from app.services.skill_extractor import extract_skills


def test_extracts_multiple_skills():
    skills = extract_skills(
        "Experience with Python, FastAPI, PostgreSQL and Docker."
    )

    assert skills == {"python", "fastapi", "postgresql", "docker"}


def test_normalizes_aliases():
    skills = extract_skills("Built infrastructure using AWS and K8s.")

    assert skills == {"aws", "kubernetes"}


def test_does_not_match_skill_inside_an_unrelated_word():
    assert extract_skills("We need a JavaScript developer.") == {
        "javascript"
    }


def test_empty_text_returns_no_skills():
    assert extract_skills(None) == set()
    assert extract_skills("") == set()
