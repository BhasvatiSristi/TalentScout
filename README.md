# TalentScout - AI Hiring Assistant Chatbot

TalentScout is an AI-assisted Hiring Assistant chatbot workflow that streamlines early-stage candidate screening. It combines resume parsing, ATS-style skill scoring, technical question generation, interview answer capture, and final confidence feedback in one integrated system.

## Project Overview

This project is designed to help recruiters and interviewers standardize initial screening.

Key capabilities:
1. Candidate intake with validation (name, email, phone, role).
2. Resume PDF upload and text extraction.
3. Role-based skill extraction and ATS score calculation.
4. AI-generated technical interview questions using Mistral.
5. Deterministic fallback questions when LLM is unavailable.
6. Interview answer storage with session timing.
7. Final confidence score submission and summary email.

High-level flow:
1. Intake candidate data.
2. Upload resume and extract text.
3. Compute ATS score from role-skill matching.
4. Generate interview questions.
5. Submit interview answers.
6. Submit feedback and send email summary.

## Installation Instructions
### Prerequisites
- Python 3.10+
- pip
- Internet access for Mistral API (optional if fallback is acceptable)
- SMTP credentials for email notifications

### 1) Clone the Repository
```bash
git clone <your-repo-url>
cd AI_screening_agent
```

### 2) Create and Activate Virtual Environment
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

### 4) Configure Environment Variables
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

### 5) Run Backend (FastAPI)
```bash
uvicorn app.main:app --reload
```

Backend docs:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### 6) Run Frontend (Streamlit)
Open a new terminal:
```bash
streamlit run frontend/app.py
```

Typical frontend URL: http://localhost:8501

### 7) Optional: Verify Mistral Connectivity
```bash
python api_check.py
```

## Usage Guide

1. Open Streamlit UI.
2. Enter candidate name, email, phone, and choose job role.
3. Upload a PDF resume and submit.
4. Review generated interview questions.
5. Fill answers for all questions and submit.
6. Submit final confidence score (1-10).
7. Check success/warning status for feedback and email.

Recommended run order:
1. Start FastAPI backend first.
2. Start Streamlit frontend second.
3. Complete intake before resume upload.
4. Complete resume upload before interview answer submission.
5. Submit feedback after answers are saved.

## Technical Details

### Libraries Used
- `fastapi` - API framework.
- `uvicorn[standard]` - ASGI server.
- `streamlit` - Frontend application.
- `requests` - HTTP requests from frontend and LLM integration.
- `pydantic` - Request/response validation.
- `email-validator` - Email format validation.
- `pdfplumber` - Resume PDF text extraction.
- `sqlalchemy` - ORM and database access.
- `psycopg2-binary` - PostgreSQL driver support.
- `python-dotenv` - Environment variable loading.

### Model Details (LLM)
- LLM API: Mistral Chat Completions.
- Endpoint: `https://api.mistral.ai/v1/chat/completions`
- Default model: `open-mistral-7b` (override with `MISTRAL_MODEL`).
- Request timeout: 40 seconds.
- Required output format: JSON object containing `questions` list.
- Target output: 10-12 interview-ready technical questions.
- Fallback: template questions if API key missing, HTTP/network issues, or parse failures.

### Architectural Decisions
- Layered architecture:
  - Routes: HTTP and status mapping.
  - Services: business logic and orchestration.
  - Schemas: validation and serialization.
  - Models: persistent data definition.
- Startup table creation via SQLAlchemy `create_all` for fast local setup.
- Graceful degradation:
  - LLM failures do not block question generation.
  - Email failures do not block feedback persistence.
- Interview workflow integrity:
  - Interview session initialized during resume processing.
  - Answer submission checks session existence.
- ATS scoring is deterministic and role-skill map driven for explainability.

### API Endpoints
Base URL (local): `http://127.0.0.1:8000`

1. `POST /candidates/intake`
- Creates candidate record.
- `409` if candidate email already exists.

2. `POST /candidates/resume/upload`
- Accepts multipart form-data: `candidate_id`, `job_role`, `file` (PDF).
- Returns extracted text, skills, ATS score, and interview questions.

3. `POST /candidates/interview-answers/submit`
- Saves question-answer pairs.
- Returns stored records with interview timestamps.

4. `POST /submit-feedback`
- Saves final confidence score.
- Attempts summary email send and returns email status.

5. `GET /`
- Basic health/status message.

### Data Model Snapshot
- `candidates`: id, name, email (unique), phone, job_role, created_at.
- `resumes`: id, candidate_id, file_name, extracted_text, ats_score, created_at.
- `interview_sessions`: id, candidate_id (unique), started_at, submitted_at, total_time_seconds, created_at.
- `interview_answers`: id, candidate_id, question, answer, interview_started_at, interview_submitted_at, created_at.
- `feedback`: id, candidate_id, confidence_score, created_at.

## Prompt Design

Prompt design is implemented in `app/services/interview_service.py` and follows a constrained two-message strategy:

1. System prompt
- Sets role: expert technical interviewer.
- Forces output contract: JSON only.
- Specifies schema: `{ "questions": ["q1", ...] }`.
- Restricts extra keys/markdown.

2. User prompt
- Injects job role, extracted skills, missing skills, and trimmed resume content.
- Adds generation constraints:
  - 10-12 questions.
  - practical + fundamentals + problem-solving balance.
  - emphasize missing skills.
  - concise, non-duplicate questions.

Why this works:
- Structured-output prompting reduces parser errors.
- Explicit constraints improve relevance and consistency.
- Missing-skill emphasis improves evaluation depth.
- Resume text trimming controls token usage and payload size.

Reliability safeguards:
- JSON parse recovery attempts.
- Plain-text line extraction fallback when needed.
- Final deterministic fallback questions if valid set (<10) is not produced.

## Challenges & Solutions

1. Challenge: LLM output can be malformed or wrapped in markdown.
- Solution: strict JSON response contract + resilient parsing logic + fallback question templates.

2. Challenge: External API failures/timeouts can interrupt flow.
- Solution: robust exception handling and graceful fallback generation.

3. Challenge: Some users submit interview answers before a session exists.
- Solution: initialize session during resume upload and enforce session check before saving answers.

4. Challenge: Resume PDFs may be empty, invalid, or unreadable.
- Solution: file type/content checks and explicit extraction error messaging.

5. Challenge: SMTP issues can fail email dispatch.
- Solution: decouple email delivery from feedback save; return `email_sent` and `email_error` fields.

6. Challenge: Duplicate candidate registration by email.
- Solution: DB unique constraint and conflict mapping (`409`) in API layer.

## Repository Structure

```text
AI_screening_agent/
├── .env
├── api_check.py
├── requirements.txt
├── talentscout.db
├── app/
│   ├── database.py
│   ├── main.py
│   ├── models/
│   │   ├── candidate.py
│   │   ├── feedback.py
│   │   ├── interview_answer.py
│   │   ├── interview_session.py
│   │   └── resume.py
│   ├── routes/
│   │   ├── candidates.py
│   │   ├── feedback.py
│   │   ├── interview_answers.py
│   │   └── resume.py
│   ├── schemas/
│   │   ├── candidate.py
│   │   ├── feedback.py
│   │   ├── interview_answer.py
│   │   └── resume.py
│   └── services/
│       ├── candidate_service.py
│       ├── email_service.py
│       ├── feedback_service.py
│       ├── interview_service.py
│       ├── resume_service.py
│       └── scoring_service.py
└── frontend/
    └── app.py
```

## File-by-File Summary

### Root
- `.env`: Runtime secrets/config.
- `requirements.txt`: Dependency list.
- `api_check.py`: Mistral API sanity check script.
- `talentscout.db`: Default SQLite database.

### Backend
- `app/main.py`: App bootstrap, router registration, startup table creation.
- `app/database.py`: Engine/session setup, DB compatibility handling.
- `app/routes/*`: API controllers.
- `app/services/*`: Business logic.
- `app/schemas/*`: Request/response contracts.
- `app/models/*`: Persistent entity definitions.

### Frontend
- `frontend/app.py`: Streamlit UI and backend integration.

## Error Handling and Fallbacks

- Duplicate email: HTTP `409`.
- Invalid/empty/non-PDF resume: HTTP `400`.
- Candidate not found: HTTP `404` on relevant endpoints.
- Interview answers before session setup: HTTP `400`.
- Mistral errors: graceful fallback questions.
- SMTP failures: feedback still saved; email status returned.

## Current Role-Skill Mapping Coverage

- Frontend Developer
- Backend Developer
- Full Stack Developer
- Data Analyst
- Data Scientist
- AI Engineer
- ML Engineer
- Software Engineer

## Future Improvements

1. Add authentication and role-based access.
2. Add migration tooling (Alembic).
3. Improve skill extraction with richer NLP methods.
4. Add unit/integration tests and CI.
5. Add Docker and deployment manifests.
