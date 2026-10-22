
from app.models.candidate import Candidate
from app.models.job import Job


def calculate_match_score(candidate: Candidate, job: Job) -> float:
    """
    Calculate a simple job-title match score from 0 to 100.
    This first version compares the candidate's target role
    with the job title.
    """
    if not candidate.target_role or not job.title:
        return 0.0

    target_role = candidate.target_role.strip().lower()
    job_title = job.title.strip().lower()

    if not target_role or not job_title:
        return 0.0

    if target_role == job_title:
        return 100.0

    if target_role in job_title:
        return 80.0

    if job_title in target_role:
        return 70.0

    
    target_words = set(target_role.split())
    job_words = set(job_title.split())

    generic_words = {
        "developer",
        "engineer",
        "senior",
        "junior",
        "lead",
        "associate",
        "software",
    }

    target_specific = target_words - generic_words
    job_specific = job_words - generic_words

    if not target_specific:
        return 0.0

    overlap = target_specific.intersection(job_specific)

    if not overlap:
        return 0.0

    score = len(overlap) / len(target_specific) * 60.0

    return round(min(score, 60.0), 2)



def rank_jobs_for_candidate(
    candidate: Candidate,
    jobs: list[Job],
) -> list[dict]:
    """Return jobs ranked by their title match score."""
    ranked_jobs = []

    for job in jobs:
        score = calculate_match_score(candidate, job)

        ranked_jobs.append(
            {
                "job": job,
                "match_score": score,
            }
        )

    return sorted(
        ranked_jobs,
        key=lambda item: item["match_score"],
        reverse=True,
    )

