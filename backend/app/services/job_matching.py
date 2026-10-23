
import re

from app.models.candidate import Candidate
from app.models.job import Job
from app.services.skill_extractor import extract_skills


ROLE_WEIGHT = 0.60
SKILL_WEIGHT = 0.40

MIN_ROLE_SCORE = 30.0
MIN_MATCH_SCORE = 25.0


def _normalize_text(text: str | None) -> str:
    return (text or "").strip().lower()


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9+#.]+", text.lower()))


def _calculate_role_score(
    target_role: str,
    job_title: str,
) -> float:
    target = _normalize_text(target_role)
    title = _normalize_text(job_title)

    if not target or not title:
        return 0.0

    if target == title:
        return 100.0

    if re.search(rf"(?<!\w){re.escape(target)}(?!\w)", title):
        return 90.0

    if re.search(rf"(?<!\w){re.escape(title)}(?!\w)", target):
        return 80.0

    target_words = _tokenize(target)
    job_words = _tokenize(title)

    # Generic words do not establish role relevance by themselves.

    # Ignore generic seniority and job-family words when
    # comparing the specific technical specialization.
    generic_words = {
        "developer",
        "engineer",
        "senior",
        "junior",
        "lead",
        "principal",
        "staff",
        "associate",
        "manager",
        "specialist",
        "analyst",
        "architect",
    }

    target_specific = target_words - generic_words
    job_specific = job_words - generic_words

    # Shared specialization is strong evidence of relevance.
    overlap = target_specific & job_specific

    if overlap and target_specific:
        return round(
            len(overlap) / len(target_specific) * 60.0,
            2,
        )

    # Allow a related backend role for a Python Developer,
    # but do not treat generic words as a match on their own.
    backend_roles = {
        "python developer",
        "backend developer",
        "backend engineer",
        "software engineer",
        "software developer",
    }

    if target in backend_roles and title in backend_roles:
        return 45.0

    return 0.0





def _candidate_skills(candidate: Candidate) -> set[str]:
    skills: set[str] = set()

    for skill in candidate.skills or []:
        skills.update(extract_skills(skill))

    return skills


def _job_skills(job: Job) -> set[str]:
    # Include the title because some listings have short descriptions.
    text = f"{job.title or ''}\n{job.description or ''}"
    return extract_skills(text)


def calculate_match_details(
    candidate: Candidate,
    job: Job,
) -> dict:
    """Return an explainable score and skill comparison for a candidate."""
    target_role = _normalize_text(candidate.target_role)
    job_title = _normalize_text(job.title)

    role_score = (
        _calculate_role_score(target_role, job_title)
        if target_role and job_title
        else 0.0
    )

    candidate_skills = _candidate_skills(candidate)
    job_skills = _job_skills(job)

    matching_skills = sorted(candidate_skills & job_skills)
    missing_skills = sorted(job_skills - candidate_skills)

    # Measure how many recognized job skills are covered by the profile.
    skill_score = (
        round(len(matching_skills) / len(job_skills) * 100.0, 2)
        if job_skills
        else 0.0
    )

    # Preserve the existing behavior: a missing role or title gives zero.
    # Jobs without a target role or job title cannot be recommended.
    if not target_role or not job_title:
        match_score = 0.0

    # A strong skill overlap must not compensate for an unrelated role.
    elif role_score < MIN_ROLE_SCORE:
        match_score = 0.0

    else:
        match_score = round(
            role_score * ROLE_WEIGHT + skill_score * SKILL_WEIGHT,
            2,
        )

    if match_score < MIN_MATCH_SCORE:
        match_score = 0.0


    if not job_skills:
        explanation = (
            "No recognized skills were found in this job listing, "
            "so skill coverage could not be assessed."
        )
    elif matching_skills and missing_skills:
        explanation = (
            f"Your profile matches {len(matching_skills)} of "
            f"{len(job_skills)} recognized job skills. "
            f"Skills mentioned in the listing but absent from your "
            f"profile: {', '.join(missing_skills)}."
        )
    elif matching_skills:
        explanation = (
            f"Your profile contains all {len(job_skills)} "
            "recognized skills found in this listing."
        )
    else:
        explanation = (
            f"None of the {len(job_skills)} recognized skills "
            "found in this listing appear in your profile. "
            f"Review: {', '.join(missing_skills)}."
        )


    return {
        "match_score": match_score,
        "role_score": role_score,
        "skill_score": skill_score,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "explanation": explanation,
    }


def calculate_match_score(candidate: Candidate, job: Job) -> float:
    return calculate_match_details(candidate, job)["match_score"]


def rank_jobs_for_candidate(
    candidate: Candidate,
    jobs: list[Job],
) -> list[dict]:
    """Rank every job from highest to lowest combined match score."""
    ranked_jobs = [
        {
            "job": job,
            "match_score": calculate_match_score(candidate, job),
        }
        for job in jobs
    ]

    return sorted(
        ranked_jobs,
        key=lambda item: item["match_score"],
        reverse=True,
    )
