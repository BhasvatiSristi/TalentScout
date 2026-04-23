"""
Purpose: Handles interview question generation and answer submission.

Inputs:

* Candidate id and submitted question-answer pairs

Outputs:

* Generated interview questions and saved interview answer rows with timing

Used in:

* Called by resume processing for question generation and by answer submission routes
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Any

import requests
from sqlalchemy.orm import Session

from app.models.interview_answer import InterviewAnswer
from app.models.interview_question import InterviewQuestion
from app.models.interview_session import InterviewSession
from app.schemas.interview_answer import InterviewAnswerItem
from app.services.resume_service import CandidateNotFoundError, get_candidate_or_raise

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "open-mistral-7b")
REQUEST_TIMEOUT_SECONDS = 40

logger = logging.getLogger(__name__)


def _trim_resume_text(resume_text: str, max_chars: int = 6000) -> str:
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
    role = job_role.strip() or "this role"
    gap_focus = missing_skills[:5] if missing_skills else ["core fundamentals"]
    strength_focus = skills[:3] if skills else ["your strongest skill"]

    return [
        f"Can you briefly introduce your experience relevant to {role}?",
        f"Walk me through a project where you used {strength_focus[0]} effectively.",
        "How do you approach debugging when a production issue appears suddenly?",
        "Explain a trade-off you made in a recent technical decision.",
        f"How would you improve your proficiency in {gap_focus[0]} over the next 30 days?",
        "Describe how you prioritize tasks when deadlines are tight.",
        f"Design a small solution for {role} and explain your architecture choices.",
        "How do you test and validate your work before release?",
        "Tell me about a time you received critical feedback and what changed afterward.",
        f"If you had to learn {gap_focus[-1]} quickly for a project, what learning plan would you follow?",
    ]


def _extract_questions_from_response(content: str) -> list[str]:
    raw_content = (content or "").strip()

    if raw_content.startswith("```"):
        raw_content = raw_content.strip("`")
        raw_content = raw_content.replace("json\n", "", 1).strip()

    def normalize(items: list[Any]) -> list[str]:
        cleaned = [str(item).strip().lstrip("- ") for item in items if str(item).strip()]
        if len(cleaned) > 12:
            cleaned = cleaned[:12]
        return cleaned

    parsed: Any = None
    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError:
        start_obj = raw_content.find("{")
        end_obj = raw_content.rfind("}")
        if start_obj != -1 and end_obj != -1 and start_obj < end_obj:
            try:
                parsed = json.loads(raw_content[start_obj : end_obj + 1])
            except json.JSONDecodeError:
                parsed = None

    normalized: list[str] = []

    if isinstance(parsed, dict) and isinstance(parsed.get("questions"), list):
        normalized = normalize(parsed["questions"])
    elif isinstance(parsed, list):
        normalized = normalize(parsed)
    else:
        # Fallback for plain-text answers: accept numbered or bullet lines.
        lines = [line.strip() for line in raw_content.splitlines() if line.strip()]
        extracted = []
        for line in lines:
            match = re.match(r"^(?:\d+[\).:-]?|[-*])\s*(.+)$", line)
            if match:
                extracted.append(match.group(1).strip())

        if len(extracted) >= 8:
            normalized = normalize(extracted)

    if len(normalized) < 10:
        raise ValueError("Model response did not contain 10+ valid questions.")

    return normalized


def _load_env_from_file() -> dict[str, str]:
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
    """
    Generate interview questions with the LLM or a deterministic fallback.
    """
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

class InterviewSessionNotFoundError(Exception):
    """
    Raised when interview session was not initialized before answer submission.
    """


def get_next_interview_question(db: Session, candidate_id: int) -> dict:
    """
    Return the next pending interview question for a candidate.
    """
    get_candidate_or_raise(db=db, candidate_id=candidate_id)

    interview_session = (
        db.query(InterviewSession)
        .filter(InterviewSession.candidate_id == candidate_id)
        .first()
    )
    if interview_session is None:
        raise InterviewSessionNotFoundError("Interview session not found. Please upload resume first.")

    total_questions = (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.candidate_id == candidate_id)
        .count()
    )
    if total_questions == 0:
        raise RuntimeError("No interview questions found. Please upload resume again.")

    answered_count = (
        db.query(InterviewAnswer)
        .filter(InterviewAnswer.candidate_id == candidate_id)
        .count()
    )

    if answered_count >= total_questions:
        if interview_session.submitted_at is None:
            submitted_at = datetime.utcnow()
            total_time_seconds = round(
                max(0.0, (submitted_at - interview_session.started_at).total_seconds()),
                2,
            )
            interview_session.submitted_at = submitted_at
            interview_session.total_time_seconds = total_time_seconds
            db.commit()

        return {
            "candidate_id": candidate_id,
            "current_question_number": total_questions,
            "total_questions": total_questions,
            "question": None,
            "completed": True,
            "interview_started_at": interview_session.started_at,
            "interview_submitted_at": interview_session.submitted_at,
            "total_time_seconds": interview_session.total_time_seconds,
        }

    next_question = (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.candidate_id == candidate_id)
        .order_by(InterviewQuestion.question_order.asc())
        .offset(answered_count)
        .first()
    )
    if next_question is None:
        raise RuntimeError("Could not resolve next interview question.")

    return {
        "candidate_id": candidate_id,
        "current_question_number": answered_count + 1,
        "total_questions": total_questions,
        "question": next_question.question,
        "completed": False,
        "interview_started_at": interview_session.started_at,
        "interview_submitted_at": interview_session.submitted_at,
        "total_time_seconds": interview_session.total_time_seconds,
    }


def submit_interview_answer_step(db: Session, candidate_id: int, answer: str) -> dict:
    """
    Save one answer and return updated conversational progress.
    """
    clean_answer = answer.strip()
    if not clean_answer:
        raise RuntimeError("Answer cannot be empty.")

    next_payload = get_next_interview_question(db=db, candidate_id=candidate_id)
    if next_payload["completed"]:
        raise RuntimeError("Interview is already completed.")

    interview_session = (
        db.query(InterviewSession)
        .filter(InterviewSession.candidate_id == candidate_id)
        .first()
    )
    if interview_session is None:
        raise InterviewSessionNotFoundError("Interview session not found. Please upload resume first.")

    answer_row = InterviewAnswer(
        candidate_id=candidate_id,
        question=next_payload["question"],
        answer=clean_answer,
        interview_started_at=interview_session.started_at,
        interview_submitted_at=None,
    )

    try:
        db.add(answer_row)
        db.commit()
        return get_next_interview_question(db=db, candidate_id=candidate_id)
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Could not save interview answer.") from exc


def save_interview_answers(
    db: Session,
    candidate_id: int,
    responses: list[InterviewAnswerItem],
) -> list[InterviewAnswer]:
    """
    Save interview answers and update the interview session.

    Parameters:

    * db: SQLAlchemy database session
    * candidate_id: Candidate id linked to the interview
    * responses: List of submitted question and answer items

    Returns:

    * list[InterviewAnswer]: Saved answer rows

    Steps:

    1. Confirm the candidate exists
    2. Load the interview session started during resume upload
    3. Mark the submission time and compute total interview time
    4. Save each answer row
    5. Commit the changes and refresh the saved rows
    """
    get_candidate_or_raise(db=db, candidate_id=candidate_id)

    interview_session = (
        db.query(InterviewSession)
        .filter(InterviewSession.candidate_id == candidate_id)
        .first()
    )
    if interview_session is None:
        raise InterviewSessionNotFoundError("Interview session not found. Please upload resume first.")

    started_at = interview_session.started_at
    submitted_at = datetime.utcnow()
    total_time_seconds = round(max(0.0, (submitted_at - started_at).total_seconds()), 2)

    interview_session.submitted_at = submitted_at
    interview_session.total_time_seconds = total_time_seconds

    saved_answers: list[InterviewAnswer] = []

    try:
        for item in responses:
            answer_row = InterviewAnswer(
                candidate_id=candidate_id,
                question=item.question.strip(),
                answer=item.answer.strip(),
                interview_started_at=started_at,
                interview_submitted_at=submitted_at,
            )
            db.add(answer_row)
            saved_answers.append(answer_row)

        db.commit()

        for item in saved_answers:
            db.refresh(item)

        return saved_answers
    except Exception as exc:
        db.rollback()
        raise RuntimeError("Could not save interview answers.") from exc
