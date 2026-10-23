
import re
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.routes.candidates import get_db
from app.models.candidate import Candidate
from app.services.resume_parser import (
    MAX_RESUME_SIZE,
    ResumeParsingError,
    extract_resume_text,
)
from app.services.skill_extractor import extract_skills


router = APIRouter(prefix="/resumes", tags=["Resumes"])

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


SECTION_ALIASES = {
    "education": r"education|academic background|educational qualifications",
    "experience": (
        r"experience|work experience|professional experience|employment history"
    ),
    "projects": r"projects|personal projects|academic projects",
}

SECTION_STOP_WORDS = (
    r"education|academic background|educational qualifications|"
    r"experience|work experience|professional experience|employment history|"
    r"projects|personal projects|academic projects|"
    r"skills|technical skills|certifications|certificates|"
    r"summary|professional summary|profile|objective|"
    r"achievements|publications|languages"
)


def _extract_name(text: str) -> str | None:
    """Try to identify a plausible name near the beginning of a resume."""
    ignored = {
        "resume",
        "curriculum vitae",
        "cv",
        "profile",
        "software engineer",
        "python developer",
        "professional summary",
        "summary",
    }

    for line in text.splitlines()[:8]:
        line = line.strip()
        line = re.sub(r"^(name)\s*:\s*", "", line, flags=re.IGNORECASE)

        if not line or len(line) > 70 or "@" in line:
            continue

        if any(char.isdigit() for char in line):
            continue

        if line.lower() in ignored:
            continue

        # Reject likely headings and lines that look like contact details.
        if re.search(
            r"\b(phone|mobile|email|linkedin|github|address|portfolio)\b",
            line,
            re.IGNORECASE,
        ):
            continue

        words = re.findall(r"[A-Za-z][A-Za-z.'-]*", line)
        if 2 <= len(words) <= 4 and len(words) == len(line.split()):
            return line

    return None


def _extract_section(text: str, section_name: str) -> list[str]:
    """Extract lines under a recognized heading until the next heading."""
    heading_pattern = SECTION_ALIASES[section_name]

    pattern = re.compile(
        rf"(?im)^[ \t]*(?:{heading_pattern})[ \t]*[:\-]?[ \t]*$"
    )
    match = pattern.search(text)

    if not match:
        return []

    remaining = text[match.end():]
    stop_pattern = re.compile(
        rf"(?im)^[ \t]*(?:{SECTION_STOP_WORDS})[ \t]*[:\-]?[ \t]*$"
    )
    stop_match = stop_pattern.search(remaining)

    if stop_match:
        remaining = remaining[:stop_match.start()]

    return [
        line.strip(" \t•-*")
        for line in remaining.splitlines()
        if line.strip(" \t•-*")
    ]


def _normalize_phone(raw_phone: str | None) -> str | None:
    """Normalize a phone number while preserving an international prefix."""
    if not raw_phone:
        return None

    digits = re.sub(r"\D", "", raw_phone)

    # Normalize Indian numbers when the country code is present.
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]

    if len(digits) < 10 or len(digits) > 15:
        return None

    if len(digits) == 10:
        return digits

    if raw_phone.strip().startswith("+"):
        return f"+{digits}"

    return digits


def _extract_profile_sections(text: str) -> dict[str, list[str]]:
    return {
        section_name: _extract_section(text, section_name)
        for section_name in SECTION_ALIASES
    }



@router.post("/{candidate_id}/parse")
async def upload_and_parse_resume(
    candidate_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_db),
):
    candidate = session.get(Candidate, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found",
        )

    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported",
        )

    content = await file.read(MAX_RESUME_SIZE + 1)

    try:
        text = extract_resume_text(filename, content)
    except ResumeParsingError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    finally:
        await file.close()

    
    email_match = re.search(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        text,
    )

    # Look for a phone-like sequence, then normalize it.
    phone_match = re.search(
        r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)",
        text,
    )
    phone = _normalize_phone(phone_match.group(0)) if phone_match else None

    suggested_skills = sorted(set(extract_skills(text)))
    sections = _extract_profile_sections(text)

    return {
        "candidate_id": candidate.id,
        "original_filename": filename,
        "extracted_text": text,
        "profile_draft": {
            "full_name": _extract_name(text),
            "email": email_match.group(0) if email_match else None,
            "phone": phone,
            "target_role": None,
            "skills": suggested_skills,
            "education": sections["education"],
            "experience": sections["experience"],
            "projects": sections["projects"],
            "needs_review": True,
        },
        "message": (
            "Resume parsed successfully. Review the draft before "
            "updating the candidate profile."
        ),
    }

