"""
Purpose: Scores resumes by matching keywords to role requirements.

Inputs:

* Resume text and the selected job role

Outputs:

* Extracted skills, matched skills, and an ATS-style percentage score

Used in:

* Called by the resume service during resume processing
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
    """
    Normalize text for easier keyword matching.

    Parameters:

    * text: Free-form text from a resume or job role

    Returns:

    * str: Lowercased text with repeated spaces removed

    Steps:

    1. Convert the text to lowercase
    2. Replace repeated whitespace with single spaces
    3. Trim outer spaces
    """
    return re.sub(r"\s+", " ", text.lower()).strip()


def extract_skills(text: str) -> list[str]:
    """
    Extract known skills from resume text.

    Parameters:

    * text: Resume text to scan

    Returns:

    * list[str]: Sorted list of matched skills

    Steps:

    1. Normalize the resume text
    2. Search for each known skill keyword
    3. Remove duplicates and sort the result
    """
    normalized_text = normalize_text(text)
    extracted = [skill for skill in COMMON_SKILLS if skill in normalized_text]
    return sorted(set(extracted))


def get_required_skills(job_role: str) -> list[str]:
    """
    Get the required skills for a job role.

    Parameters:

    * job_role: Job role selected by the user

    Returns:

    * list[str]: Skills mapped to that role

    Steps:

    1. Normalize the role name
    2. Look up the role in the skill map
    3. Return the matching skill list or an empty list
    """
    role_key = normalize_text(job_role)
    return ROLE_SKILL_MAP.get(role_key, [])


def match_skills(candidate_skills: list[str], required_skills: list[str]) -> list[str]:
    """
    Find the overlap between candidate skills and required skills.

    Parameters:

    * candidate_skills: Skills found in the resume
    * required_skills: Skills needed for the selected role

    Returns:

    * list[str]: Sorted list of skills found in both lists

    Steps:

    1. Convert both lists to lowercase sets
    2. Find the shared values
    3. Return the matches in sorted order
    """
    candidate_set = {skill.lower() for skill in candidate_skills}
    required_set = {skill.lower() for skill in required_skills}
    return sorted(candidate_set.intersection(required_set))


def calculate_ats_score(matched_skills: list[str], required_skills: list[str]) -> float:
    """
    Calculate a simple ATS-style score from skill coverage.

    Parameters:

    * matched_skills: Skills found in both the resume and the role
    * required_skills: Skills expected for the role

    Returns:

    * float: Percentage score rounded to two decimal places

    Steps:

    1. Return 0 if there are no required skills
    2. Divide matched skills by required skills
    3. Convert the result to a percentage
    4. Round the final score
    """
    if not required_skills:
        return 0.0

    score = (len(matched_skills) / len(required_skills)) * 100
    return round(score, 2)