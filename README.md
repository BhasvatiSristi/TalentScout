# TalentScout - AI Screening Agent

A full-stack AI-assisted candidate screening workflow built with FastAPI (backend), Streamlit (frontend), SQLAlchemy (database layer), and Mistral AI (interview question generation).

The project flow is:
1. Capture candidate intake details.
2. Upload and parse resume PDF.
3. Extract skills and compute ATS-style score.
4. Generate interview questions (LLM with fallback).
5. Save interview answers and interview duration.
6. Submit final confidence score and send summary email.

## Tech Stack

### Backend
- FastAPI
- Uvicorn
- SQLAlchemy
- Pydantic
- python-dotenv

### Frontend
- Streamlit
- requests

### AI + Document Processing
- Mistral Chat Completions API
- pdfplumber

### Data + Infra
- SQLite (default)
- PostgreSQL (supported via DATABASE_URL)
- SMTP (email notifications)

### Runtime + Validation
- Python 3.10+
- email-validator

## Repository Structure

```text
AI_screening_agent/
├── .env
├── api_check.py
├── requirements.txt
├── talentscout.db
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── main.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── candidate.py
│   │   ├── feedback.py
│   │   ├── interview_answer.py
│   │   ├── interview_session.py
│   │   └── resume.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── candidates.py
│   │   ├── feedback.py
│   │   ├── interview_answers.py
│   │   └── resume.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── candidate.py
│   │   ├── feedback.py
│   │   ├── interview_answer.py
│   │   └── resume.py
│   └── services/
│       ├── __init__.py
│       ├── candidate_service.py
│       ├── email_service.py
│       ├── feedback_service.py
│       ├── interview_service.py
│       ├── resume_service.py
│       └── scoring_service.py
└── frontend/
    └── app.py
```

## File-by-File Purpose

### Root
- `.env`: Runtime secrets/config (Mistral, DB URL, SMTP).
- `requirements.txt`: Python dependencies.
- `api_check.py`: Quick script to validate Mistral API key/connectivity.
- `talentscout.db`: Default SQLite database file.

### Backend Core
- `app/main.py`: FastAPI app bootstrap, router registration, startup table creation, root health endpoint.
- `app/database.py`: SQLAlchemy engine/session setup, `.env` loading, SQLite/Postgres handling, `get_db()` dependency.
- `app/__init__.py`: Package marker.

### Models (Database Tables)
- `app/models/candidate.py`: Candidate profile (name, email, phone, job role).
- `app/models/resume.py`: Resume metadata + extracted text + ATS score.
- `app/models/interview_session.py`: Interview timing (start, submit, total seconds).
- `app/models/interview_answer.py`: Saved Q/A responses.
- `app/models/feedback.py`: Final confidence score.
- `app/models/__init__.py`: Package marker.

### Routes (API Layer)
- `app/routes/candidates.py`: Candidate intake endpoint.
- `app/routes/resume.py`: Resume upload + extraction + scoring endpoint.
- `app/routes/interview_answers.py`: Interview answer submission endpoint.
- `app/routes/feedback.py`: Final feedback submission endpoint.
- `app/routes/__init__.py`: Package marker.

### Schemas (Validation + Serialization)
- `app/schemas/candidate.py`: Candidate request/response models.
- `app/schemas/resume.py`: Resume response models.
- `app/schemas/interview_answer.py`: Interview answers request/response models.
- `app/schemas/feedback.py`: Feedback request model.
- `app/schemas/__init__.py`: Package marker.

### Services (Business Logic)
- `app/services/candidate_service.py`: Candidate creation + duplicate email handling.
- `app/services/resume_service.py`: PDF text extraction, skills/ATS orchestration, interview session start.
- `app/services/interview_service.py`: LLM question generation, fallback questions, answer persistence.
- `app/services/scoring_service.py`: Skill extraction/matching + ATS scoring.
- `app/services/feedback_service.py`: Feedback persistence + email dispatch orchestration.
- `app/services/email_service.py`: SMTP email sending.
- `app/services/__init__.py`: Package marker.

### Frontend
- `frontend/app.py`: Streamlit UI for full screening workflow and backend API calls.

## API Overview

Base URL (local): `http://127.0.0.1:8000`

### 1) Candidate Intake
- Method: `POST`
- Path: `/candidates/intake`
- Request JSON:

```json
{
  "name": "Asha Khan",
  "email": "asha@example.com",
  "phone": "9876543210",
  "job_role": "Frontend Developer"
}
```

- Success: `200`
- Conflict: `409` (duplicate email)

### 2) Resume Upload + Processing
- Method: `POST`
- Path: `/candidates/resume/upload`
- Request: `multipart/form-data`
  - `candidate_id` (int)
  - `job_role` (string)
  - `file` (PDF)

- Success: `200`
- Errors: `400` (invalid/empty PDF), `404` (candidate not found)

### 3) Interview Answers Submission
- Method: `POST`
- Path: `/candidates/interview-answers/submit`
- Request JSON:

```json
{
  "candidate_id": 1,
  "responses": [
    {
      "question": "Explain event bubbling in JavaScript.",
      "answer": "Event bubbling is..."
    }
  ]
}
```

- Success: `200`
- Errors: `400` (session not initialized), `404` (candidate not found)

### 4) Final Feedback Submission
- Method: `POST`
- Path: `/submit-feedback`
- Request JSON:

```json
{
  "candidate_id": 1,
  "confidence_score": 8
}
```

- Success: `200`
- Errors: `404` (candidate not found)

### 5) Root Health
- Method: `GET`
- Path: `/`

## Data Model Snapshot

- `candidates`
  - `id`, `name`, `email` (unique), `phone`, `job_role`, `created_at`
- `resumes`
  - `id`, `candidate_id`, `file_name`, `extracted_text`, `ats_score`, `created_at`
- `interview_sessions`
  - `id`, `candidate_id` (unique), `started_at`, `submitted_at`, `total_time_seconds`, `created_at`
- `interview_answers`
  - `id`, `candidate_id`, `question`, `answer`, `interview_started_at`, `interview_submitted_at`, `created_at`
- `feedback`
  - `id`, `candidate_id`, `confidence_score`, `created_at`

## Environment Variables

Create/update `.env` in project root:

```env
# AI model
MISTRAL_API_KEY=your_mistral_api_key
MISTRAL_MODEL=open-mistral-7b

# Database
DATABASE_URL=sqlite:///./talentscout.db

# SMTP email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@example.com
SMTP_PASSWORD=your_email_password_or_app_password
EMAIL_FROM=your_email@example.com
```

Notes:
- If `MISTRAL_API_KEY` is missing or request fails, the app uses deterministic fallback interview questions.
- If SMTP credentials are missing/invalid, feedback is still saved, and email failure is returned in response metadata.

## Local Setup

### 1) Clone and Enter
```bash
git clone <your-repo-url>
cd AI_screening_agent
```

### 2) Create Virtual Environment
Windows PowerShell:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3) Install Dependencies
```bash
pip install -r requirements.txt
```

### 4) Configure Environment
- Add `.env` values shown above.

### 5) Run Backend (FastAPI)
```bash
uvicorn app.main:app --reload
```

Backend docs:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### 6) Run Frontend (Streamlit)
Open a new terminal:
```bash
streamlit run frontend/app.py
```

Frontend URL is shown by Streamlit (typically `http://localhost:8501`).

## End-to-End Workflow

1. User fills candidate details and selects role in Streamlit.
2. Frontend calls `/candidates/intake`.
3. User uploads PDF resume; frontend calls `/candidates/resume/upload`.
4. Backend:
   - extracts PDF text (`pdfplumber`),
   - extracts/matches skills,
   - computes ATS score,
   - generates 10-12 interview questions (Mistral or fallback),
   - creates/updates interview session start time.
5. Frontend renders generated questions and submits answers to `/candidates/interview-answers/submit`.
6. Backend saves answers and interview timing.
7. User submits confidence score to `/submit-feedback`.
8. Backend stores feedback, fetches latest ATS score, and sends summary email.

## Error Handling and Fallbacks

- Duplicate candidate email returns `409 Conflict`.
- Non-PDF, empty, or unreadable resume returns `400`.
- Missing candidate returns `404` in relevant endpoints.
- Interview answers before resume upload return `400` (session missing).
- Mistral API/network/parsing issues gracefully fallback to template questions.
- SMTP send failures do not block feedback persistence.

## Useful Utility Script

Run Mistral API check:
```bash
python api_check.py
```

Expected:
- Prints HTTP status code and JSON response from Mistral chat completions endpoint.

## Dependencies (from requirements.txt)

- `fastapi`
- `uvicorn[standard]`
- `streamlit`
- `requests`
- `pydantic`
- `email-validator`
- `pdfplumber`
- `sqlalchemy`
- `psycopg2-binary`
- `python-dotenv`

## Current Job Roles in Skill Mapping

The ATS scoring role map currently supports:
- Frontend Developer
- Backend Developer
- Full Stack Developer
- Data Analyst
- Data Scientist
- AI Engineer
- ML Engineer
- Software Engineer

## Future Improvements

- Add authentication/authorization for admin screening panel.
- Add migration tooling (Alembic) instead of startup `create_all` only.
- Improve NLP skill extraction beyond keyword matching.
- Add automated tests (unit + API integration).
- Add Docker and CI workflow for deployment.
