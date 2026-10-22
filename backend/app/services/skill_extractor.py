
import re

# Extend this vocabulary as needed. Matching logic remains generic.
SKILL_VOCABULARY = {
    "python": ["python"],
    "java": ["java"],
    "javascript": ["javascript", "js"],
    "typescript": ["typescript", "ts"],
    "c++": ["c++", "cpp"],
    "sql": ["sql"],
    "postgresql": ["postgresql", "postgres"],
    "mysql": ["mysql"],
    "fastapi": ["fastapi"],
    "django": ["django"],
    "flask": ["flask"],
    "react": ["react", "react.js"],
    "node.js": ["node.js", "nodejs"],
    "aws": ["aws", "amazon web services"],
    "azure": ["microsoft azure", "azure"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "git": ["git"],
    "linux": ["linux"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning"],
    "pytorch": ["pytorch"],
    "tensorflow": ["tensorflow"],
    "airflow": ["airflow", "apache airflow"],
    "databricks": ["databricks"],
    "rest api": ["rest api", "restful api", "rest apis"],
}


def _contains_term(text: str, term: str) -> bool:
    """Match a term without accidentally matching it inside a larger word."""
    pattern = rf"(?<!\w){re.escape(term.lower())}(?!\w)"
    return re.search(pattern, text.lower()) is not None


def extract_skills(text: str | None) -> set[str]:
    """Return canonical skills found in a text using a reusable vocabulary."""
    if not text:
        return set()

    found = set()

    for canonical_skill, aliases in SKILL_VOCABULARY.items():
        if any(_contains_term(text, alias) for alias in aliases):
            found.add(canonical_skill)

    return found
