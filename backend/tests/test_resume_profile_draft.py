
from app.api.routes.resumes import (
    _extract_name,
    _extract_profile_sections,
    _normalize_phone,
)


def test_extract_name_from_resume_header():
    text = """Kausik Naskar
kausik@example.com
+91 9876543210

EDUCATION
B.Tech in Computer Science
"""
    assert _extract_name(text) == "Kausik Naskar"


def test_name_is_none_when_no_plausible_name_exists():
    text = """Python Developer
kausik@example.com
+91 9876543210
"""
    assert _extract_name(text) is None


def test_normalize_indian_phone_number():
    assert _normalize_phone("+91 9876543210") == "9876543210"


def test_normalize_phone_rejects_invalid_number():
    assert _normalize_phone("12345") is None


def test_extract_education_experience_and_projects():
    text = """EDUCATION
B.Tech in Computer Science
ABC University

EXPERIENCE
Software Developer at XYZ
Worked with Python and FastAPI

PROJECTS
Agentic Job Hunter
Built a job-matching backend

SKILLS
Python, FastAPI
"""
    sections = _extract_profile_sections(text)

    assert "B.Tech in Computer Science" in sections["education"]
    assert "Software Developer at XYZ" in sections["experience"]
    assert "Agentic Job Hunter" in sections["projects"]
    assert "Python, FastAPI" not in sections["projects"]
