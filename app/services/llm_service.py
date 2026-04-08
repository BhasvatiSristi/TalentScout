"""
LLM-backed interview question generation service.

This module calls the Mistral Chat Completions API to generate role-aware
interview questions using resume context and ATS skill gaps.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import requests

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "open-mistral-7b")
REQUEST_TIMEOUT_SECONDS = 40

logger = logging.getLogger(__name__)


def _trim_resume_text(resume_text: str, max_chars: int = 6000) -> str:
    """Trim large resume text to keep token usage predictable."""
    cleaned = (resume_text or "").strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars]


def _build_messages(
    job_role: str,
    resume_text: str,
    skills: list[str],
    missing_skills: list[str],
) -> list[dict[str, str]]:
    """Build system and user prompts for reliable JSON output."""
    system_prompt = (
        "You are an expert technical interviewer. "
        "Generate practical, role-specific interview questions. "
        "Return ONLY valid JSON with this schema: "
        "{\"questions\": [\"q1\", \"q2\", ...]}. "
        "Generate 10 to 12 questions, no markdown, no extra keys."
    )

    user_prompt = (
        f"Job role: {job_role}\n"
        f"Extracted skills: {skills}\n"
        f"Missing skills: {missing_skills}\n"
        "Resume text (trimmed):\n"
        f"{_trim_resume_text(resume_text)}\n\n"
        "Requirements for questions:\n"
        "1) 10-12 questions total.\n"
        "2) Blend fundamentals, practical scenarios, and problem-solving.\n"
        "3) Prioritize missing skills for improvement-focused questions.\n"
        "4) Keep each question concise and interview-ready.\n"
        "5) Avoid duplicates and generic filler."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _fallback_questions(job_role: str, skills: list[str], missing_skills: list[str]) -> list[str]:
    """Return deterministic questions when API fails, keeping endpoint usable."""
    role = job_role.strip() or "this role"
    gap_focus = missing_skills[:5] if missing_skills else ["core fundamentals"]
    strength_focus = skills[:3] if skills else ["your strongest skill"]

    questions = [
        f"Can you briefly introduce your experience relevant to {role}?",
        f"Walk me through a project where you used {strength_focus[0]} effectively.",
        f"How do you approach debugging when a production issue appears suddenly?",
        f"Explain a trade-off you made in a recent technical decision.",
        f"How would you improve your proficiency in {gap_focus[0]} over the next 30 days?",
        f"Describe how you prioritize tasks when deadlines are tight.",
        f"Design a small solution for {role} and explain your architecture choices.",
        f"How do you test and validate your work before release?",
        f"Tell me about a time you received critical feedback and what changed afterward.",
        f"If you had to learn {gap_focus[-1]} quickly for a project, what learning plan would you follow?",
    ]

    return questions


def _extract_questions_from_response(content: str) -> list[str]:
    """Parse and validate JSON response content from the model."""
    raw_content = (content or "").strip()

    # Handle occasional fenced JSON responses.
    if raw_content.startswith("```"):
        raw_content = raw_content.strip("`")
        raw_content = raw_content.replace("json\n", "", 1).strip()

    try:
        parsed: Any = json.loads(raw_content)
    except json.JSONDecodeError:
        start = raw_content.find("{")
        end = raw_content.rfind("}")
        if start == -1 or end == -1 or start >= end:
            raise ValueError("Model response is not valid JSON.")
        parsed = json.loads(raw_content[start : end + 1])

    if not isinstance(parsed, dict):
        raise ValueError("Model response is not a JSON object.")

    questions = parsed.get("questions")
    if not isinstance(questions, list):
        raise ValueError("Model response is missing a questions list.")

    normalized = [str(question).strip() for question in questions if str(question).strip()]
    if len(normalized) < 10:
        raise ValueError("Model returned fewer than 10 questions.")

    if len(normalized) > 12:
        normalized = normalized[:12]

    return normalized


def _load_env_from_file() -> dict[str, str]:
    """Lightweight .env reader so deploy/local runs work without extra dependencies."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    loaded: dict[str, str] = {}

    if not env_path.exists():
        return loaded

    for line in env_path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue

        key, value = raw.split("=", 1)
        clean_key = key.strip()
        clean_value = value.strip().strip('"').strip("'")
        loaded[clean_key] = clean_value

    return loaded


def _get_setting(key: str, default: str = "") -> str:
    """Get setting from environment first, then fallback to .env file."""
    runtime_value = os.getenv(key, "").strip()
    if runtime_value:
        return runtime_value

    file_values = _load_env_from_file()
    return file_values.get(key, default).strip()


def generate_questions(
    job_role: str,
    resume_text: str,
    skills: list[str],
    missing_skills: list[str],
) -> list[str]:
    """Generate 10-12 interview questions using Mistral API with prompt constraints."""
    api_key = _get_setting("MISTRAL_API_KEY", "")
    if not api_key:
        logger.warning("Mistral API key not found. Falling back to template questions.")
        return _fallback_questions(job_role, skills, missing_skills)

    model_name = _get_setting("MISTRAL_MODEL", MISTRAL_MODEL)

    payload = {
        "model": model_name,
        "messages": _build_messages(job_role, resume_text, skills, missing_skills),
        "temperature": 0.4,
        "max_tokens": 800,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            MISTRAL_API_URL,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        return _extract_questions_from_response(content)
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else "unknown"
        details = exc.response.text[:300] if exc.response is not None else "no response body"
        logger.warning(
            "Mistral API request failed with status %s. Falling back. Details: %s",
            status_code,
            details,
        )
        return _fallback_questions(job_role, skills, missing_skills)
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        logger.warning("Mistral response parse failed. Falling back. Details: %s", str(exc))
        return _fallback_questions(job_role, skills, missing_skills)
    except requests.RequestException as exc:
        logger.warning("Mistral network request failed. Falling back. Details: %s", str(exc))
        return _fallback_questions(job_role, skills, missing_skills)
    except Exception as exc:
        logger.warning("Unexpected LLM error. Falling back. Details: %s", str(exc))
        return _fallback_questions(job_role, skills, missing_skills)
