
from app.models.candidate import Candidate
from app.models.job import Job
from app.services.job_matching import (
    calculate_match_score,
    rank_jobs_for_candidate,
)


def make_candidate(target_role):
    return Candidate(
        full_name="Test Candidate",
        email="candidate@example.com",
        target_role=target_role,
    )


def make_job(title, external_id="job-1"):
    return Job(
        source="lever",
        external_id=external_id,
        title=title,
        company="Example Company",
        job_url=f"https://example.com/{external_id}",
    )


def test_exact_role_match_scores_100():
    candidate = make_candidate("Python Developer")
    job = make_job("Python Developer")

    assert calculate_match_score(candidate, job) == 100.0


def test_target_role_inside_job_title_scores_80():
    candidate = make_candidate("Python Developer")
    job = make_job("Senior Python Developer")

    assert calculate_match_score(candidate, job) == 80.0


def test_unrelated_roles_score_zero():
    candidate = make_candidate("Python Developer")
    job = make_job("Java Developer")

    assert calculate_match_score(candidate, job) == 0.0


def test_missing_target_role_scores_zero():
    candidate = make_candidate(None)
    job = make_job("Python Developer")

    assert calculate_match_score(candidate, job) == 0.0


def test_jobs_are_ranked_highest_score_first():
    candidate = make_candidate("Python Developer")
    jobs = [
        make_job("Java Developer", "job-1"),
        make_job("Senior Python Developer", "job-2"),
        make_job("Python Developer", "job-3"),
    ]

    ranked = rank_jobs_for_candidate(candidate, jobs)

    assert [item["job"].title for item in ranked] == [
        "Python Developer",
        "Senior Python Developer",
        "Java Developer",
    ]
