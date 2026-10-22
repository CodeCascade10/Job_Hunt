
import re

from app.models.candidate import Candidate
from app.models.job import Job
from app.services.skill_extractor import extract_skills


ROLE_WEIGHT = 0.60
SKILL_WEIGHT = 0.40


def _normalize_text(text: str | None) -> str:
    """Normalize text for case-insensitive role comparisons."""
    return (text or "").strip().lower()


def _tokenize(text: str) -> set[str]:
    """Extract meaningful words from a job title or target role."""
    return set(re.findall(r"[a-z0-9+#.]+", text.lower()))


def _calculate_role_score(target_role: str, job_title: str) -> float:
    """Calculate role relevance on a 0-100 scale."""
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

    if not target_words:
        return 0.0

    overlap = target_words & job_words

    return round(len(overlap) / len(target_words) * 60.0, 2)


def _calculate_skill_score(
    candidate_skills: list[str] | None,
    job_description: str | None,
) -> float:
    """Calculate extracted-skill overlap on a 0-100 scale."""
    if not candidate_skills or not job_description:
        return 0.0

    normalized_candidate_skills = set()

    for skill in candidate_skills:
        normalized_candidate_skills.update(extract_skills(skill))

    if not normalized_candidate_skills:
        return 0.0

    job_skills = extract_skills(job_description)

    if not job_skills:
        return 0.0

    matching_skills = normalized_candidate_skills & job_skills

    return round(
        len(matching_skills) / len(normalized_candidate_skills) * 100.0,
        2,
    )


def calculate_match_score(candidate: Candidate, job: Job) -> float:
    """
    Combine target-role relevance and extracted-skill relevance.

    Role relevance contributes 60%.
    Skill relevance contributes 40%.
    A missing target role or job title results in zero.
    """
    target_role = _normalize_text(candidate.target_role)
    job_title = _normalize_text(job.title)

    if not target_role or not job_title:
        return 0.0

    role_score = _calculate_role_score(target_role, job_title)

    skill_score = _calculate_skill_score(
        candidate.skills,
        job.description,
    )

    combined_score = (
        role_score * ROLE_WEIGHT
        + skill_score * SKILL_WEIGHT
    )

    return round(min(100.0, max(0.0, combined_score)), 2)


def rank_jobs_for_candidate(
    candidate: Candidate,
    jobs: list[Job],
) -> list[dict]:
    """Rank jobs from highest to lowest combined match score."""
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
