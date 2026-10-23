
import pytest


from app.services.job_matching import (
    _calculate_role_score,
    calculate_match_score,
    rank_jobs_for_candidate,
)

from app.models.candidate import Candidate
from app.models.job import Job
from app.services.job_matching import (
    calculate_match_score,
    rank_jobs_for_candidate,
)


def make_candidate(
    target_role="Python Developer",
    skills=None,
):
    return Candidate(
        full_name="Test Candidate",
        email="candidate@example.com",
        target_role=target_role,
        skills=skills or [],
    )


def make_job(
    title="Python Developer",
    description="",
    company="Test Company",
):
    return Job(
        title=title,
        company=company,
        description=description,
    )

class TestCalculateRoleScore:
    def test_exact_role_match_scores_100(self):
        assert _calculate_role_score(
            "Python Developer",
            "Python Developer",
        ) == 100.0

    def test_unrelated_role_scores_zero(self):
        assert _calculate_role_score(
            "Python Developer",
            "Account Executive",
        ) == 0.0
        

class TestCalculateMatchScore:
    """Tests for role and extracted-skill based job matching."""

    def test_exact_role_match_receives_high_score(self):
        candidate = make_candidate(
            target_role="Python Developer",
            skills=["python", "fastapi"],
        )
        job = make_job(
            title="Python Developer",
            description="Python and FastAPI backend development.",
        )

        score = calculate_match_score(candidate, job)

        assert score > 0
        assert score <= 100

    def test_matching_skills_increase_relevance(self):
        candidate = make_candidate(
            target_role="Software Engineer",
            skills=["python", "fastapi", "postgresql"],
        )

        job_with_matching_skills = make_job(
            title="Software Engineer",
            description="Build services using Python, FastAPI and PostgreSQL.",
        )
        job_with_fewer_matching_skills = make_job(
            title="Software Engineer",
            description="Build services using JavaScript.",
            company="Another Company",
        )

        strong_score = calculate_match_score(
            candidate, job_with_matching_skills
        )
        weak_score = calculate_match_score(
            candidate, job_with_fewer_matching_skills
        )

        assert strong_score > weak_score

    def test_unrelated_role_and_skills_score_lower(self):
        candidate = make_candidate(
            target_role="Python Developer",
            skills=["python", "fastapi"],
        )
        job = make_job(
            title="Marketing Manager",
            description="Manage campaigns, budgets and brand strategy.",
        )

        score = calculate_match_score(candidate, job)

        assert 0 <= score < 50

    def test_no_matching_skills_does_not_create_skill_bonus(self):
        candidate = make_candidate(
            target_role="Data Engineer",
            skills=["python", "sql", "airflow"],
        )
        job = make_job(
            title="Graphic Designer",
            description="Create visual assets using design software.",
        )

        score = calculate_match_score(candidate, job)

        assert score == 0.0

    def test_skill_aliases_are_recognized(self):
        candidate = make_candidate(
            target_role="Backend Developer",
            skills=["javascript", "node.js"],
        )
        job = make_job(
            title="Backend Developer",
            description="Build APIs using JS and NodeJS.",
        )

        score = calculate_match_score(candidate, job)

        assert score > 0

    def test_empty_candidate_skills_are_handled(self):
        candidate = make_candidate(
            target_role="Python Developer",
            skills=[],
        )
        job = make_job(
            title="Python Developer",
            description="Build Python applications.",
        )

        score = calculate_match_score(candidate, job)

        assert 0 <= score <= 100

    def test_missing_target_role_returns_zero(self):
        candidate = make_candidate(
            target_role=None,
            skills=["python"],
        )
        job = make_job(
            title="Python Developer",
            description="Python backend development.",
        )

        assert calculate_match_score(candidate, job) == 0.0

    def test_missing_job_title_returns_zero(self):
        candidate = make_candidate(
            target_role="Python Developer",
            skills=["python"],
        )
        job = make_job(title=None, description="Python development.")

        assert calculate_match_score(candidate, job) == 0.0

    def test_missing_description_is_handled(self):
        candidate = make_candidate(
            target_role="Python Developer",
            skills=["python"],
        )
        job = make_job(
            title="Data Scientist",
            description=None,
        )

        score = calculate_match_score(candidate, job)

        assert 0 <= score <= 100

    def test_score_is_bounded_between_zero_and_one_hundred(self):
        candidate = make_candidate(
            target_role="Python Developer",
            skills=["python", "fastapi", "sql"],
        )
        job = make_job(
            title="Python Developer",
            description=(
                "Python, FastAPI, SQL, PostgreSQL, Docker, "
                "AWS, Linux and REST API development."
            ),
        )

        score = calculate_match_score(candidate, job)

        assert 0.0 <= score <= 100.0

    def test_candidate_skills_can_be_missing_or_none(self):
        candidate = make_candidate(target_role="Python Developer")
        candidate.skills = None

        job = make_job(
            title="Python Developer",
            description="Develop Python applications.",
        )

        score = calculate_match_score(candidate, job)

        assert 0 <= score <= 100


class TestRankJobsForCandidate:
    """Tests for sorting jobs by their combined match score."""

    def test_jobs_are_sorted_by_score_descending(self):
        candidate = make_candidate(
            target_role="Python Developer",
            skills=["python", "fastapi", "sql"],
        )
        jobs = [
            make_job(
                title="Graphic Designer",
                description="Create graphics and visual assets.",
                company="Company A",
            ),
            make_job(
                title="Python Developer",
                description="Python, FastAPI and SQL development.",
                company="Company B",
            ),
            make_job(
                title="Backend Developer",
                description="Develop services using Python and SQL.",
                company="Company C",
            ),
        ]

        ranked = rank_jobs_for_candidate(candidate, jobs)
        scores = [item["match_score"] for item in ranked]

        assert scores == sorted(scores, reverse=True)

    def test_ranking_preserves_every_job(self):
        candidate = make_candidate(
            target_role="Data Engineer",
            skills=["python", "sql"],
        )
        jobs = [
            make_job(title="Data Engineer", company="A"),
            make_job(title="Python Developer", company="B"),
            make_job(title="Designer", company="C"),
        ]

        ranked = rank_jobs_for_candidate(candidate, jobs)

        assert len(ranked) == len(jobs)
        assert {item["job"] for item in ranked} == set(jobs)

    def test_ranked_items_contain_job_and_score(self):
        candidate = make_candidate(
            target_role="Python Developer",
            skills=["python"],
        )
        job = make_job()

        ranked = rank_jobs_for_candidate(candidate, [job])

        assert len(ranked) == 1
        assert ranked[0]["job"] is job
        assert "match_score" in ranked[0]
        assert isinstance(ranked[0]["match_score"], float)

    def test_empty_job_list_returns_empty_list(self):
        candidate = make_candidate()

        assert rank_jobs_for_candidate(candidate, []) == []

    def test_equal_scores_are_allowed(self):
        candidate = make_candidate(
            target_role="Python Developer",
            skills=["python"],
        )
        jobs = [
            make_job(title="Python Developer", company="A"),
            make_job(title="Python Developer", company="B"),
        ]

        ranked = rank_jobs_for_candidate(candidate, jobs)

        assert len(ranked) == 2
        assert ranked[0]["match_score"] == ranked[1]["match_score"]
