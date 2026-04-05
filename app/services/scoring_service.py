"""
Lightweight ATS scoring utilities.

This module provides simple keyword-based skill extraction and matching.
No ML models or external APIs are used.
"""

from __future__ import annotations

import re


ROLE_SKILL_MAP = {
    "frontend developer": ["html", "css", "javascript", "react", "typescript", "git"],
    "backend developer": ["python", "fastapi", "sql", "api", "docker", "git"],
    "full stack developer": ["html", "css", "javascript", "react", "python", "sql", "git"],
    "data analyst": ["python", "sql", "excel", "power bi", "tableau", "pandas"],
    "data scientist": ["python", "pandas", "numpy", "scikit-learn", "sql", "machine learning"],
    "ai engineer": ["python", "tensorflow", "pytorch", "machine learning", "deep learning", "sql"],
    "ml engineer": ["python", "scikit-learn", "tensorflow", "pytorch", "machine learning", "sql"],
    "software engineer": ["python", "java", "c++", "git", "docker", "api"]
}


COMMON_SKILLS = sorted({skill for skills in ROLE_SKILL_MAP.values() for skill in skills})


def normalize_text(text: str) -> str:
    """Normalize free-form text for keyword matching."""
    return re.sub(r"\s+", " ", text.lower()).strip()


def extract_skills(text: str) -> list[str]:
    """Extract known skills from resume text using keyword matching."""
    normalized_text = normalize_text(text)
    extracted = [skill for skill in COMMON_SKILLS if skill in normalized_text]
    return sorted(set(extracted))


def get_required_skills(job_role: str) -> list[str]:
    """Return role-specific required skills from the mapping."""
    role_key = normalize_text(job_role)
    return ROLE_SKILL_MAP.get(role_key, [])


def match_skills(candidate_skills: list[str], required_skills: list[str]) -> list[str]:
    """Return skills present in both candidate and role requirements."""
    candidate_set = {skill.lower() for skill in candidate_skills}
    required_set = {skill.lower() for skill in required_skills}
    return sorted(candidate_set.intersection(required_set))


def calculate_ats_score(matched_skills: list[str], required_skills: list[str]) -> float:
    """Calculate ATS percentage score based on required skill coverage."""
    if not required_skills:
        return 0.0

    score = (len(matched_skills) / len(required_skills)) * 100
    return round(score, 2)