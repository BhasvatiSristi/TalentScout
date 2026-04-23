"""
Purpose: Provides the Streamlit user interface for the screening workflow.

Inputs:

* Candidate details from text fields
* Resume PDF uploaded by the user
* Interview answers and feedback values from form controls

Outputs:

* Requests sent to the FastAPI backend
* Status messages and response data shown in the browser

Used in:

* Frontend entry point that connects the user to the backend API
"""

import requests
import streamlit as st


BACKEND_URL = "http://127.0.0.1:8000"

FIELD_LABELS = {
    "name": "Name",
    "email": "Email",
    "phone": "Phone",
    "job_role": "Job Role",
    "file": "Resume",
    "confidence_score": "Confidence Score",
}

JOB_ROLE_OPTIONS = [
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "Data Analyst",
    "Data Scientist",
    "AI Engineer",
    "ML Engineer",
    "Software Engineer",
]


def submit_candidate(candidate_data: dict) -> dict:
    """
    Send candidate details to the backend intake endpoint.

    Parameters:

    * candidate_data: Dictionary with the candidate form values

    Returns:

    * dict: JSON response from the backend

    Steps:

    1. Send the candidate data to the intake endpoint
    2. Raise an error if the request fails
    3. Return the parsed JSON response
    """
    response = requests.post(f"{BACKEND_URL}/candidates/intake", json=candidate_data, timeout=30)
    response.raise_for_status()
    return response.json()


def upload_resume(resume_file, candidate_id: int, job_role: str) -> dict:
    """
    Upload a resume PDF and link it to a candidate record.

    Parameters:

    * resume_file: Uploaded resume file from Streamlit
    * candidate_id: Database id returned by candidate intake
    * job_role: Job role selected by the user

    Returns:

    * dict: JSON response from the backend

    Steps:

    1. Prepare the file payload and form data
    2. Send the upload request to the backend
    3. Return the parsed JSON response
    """
    files = {
        "file": (
            resume_file.name,
            resume_file.getvalue(),
            resume_file.type or "application/pdf",
        )
    }
    data = {"candidate_id": str(candidate_id), "job_role": job_role}
    response = requests.post(
        f"{BACKEND_URL}/candidates/resume/upload",
        data=data,
        files=files,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def submit_interview_answers(
    candidate_id: int,
    responses: list[dict[str, str]],
) -> dict:
    """
    Send interview question answers to the backend.

    Parameters:

    * candidate_id: Candidate id for the current interview session
    * responses: List of question and answer pairs

    Returns:

    * dict: JSON response from the backend

    Steps:

    1. Build the request payload
    2. Post it to the interview answers endpoint
    3. Return the parsed JSON response
    """
    payload = {
        "candidate_id": candidate_id,
        "responses": responses,
    }
    response = requests.post(
        f"{BACKEND_URL}/candidates/interview-answers/submit",
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def get_next_interview_question(candidate_id: int) -> dict:
    """
    Fetch the next conversational interview question for a candidate.
    """
    response = requests.get(
        f"{BACKEND_URL}/candidates/interview-answers/next",
        params={"candidate_id": candidate_id},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def submit_interview_answer_step(candidate_id: int, answer: str) -> dict:
    """
    Submit one conversational answer and receive updated progress.
    """
    response = requests.post(
        f"{BACKEND_URL}/candidates/interview-answers/submit-step",
        json={"candidate_id": candidate_id, "answer": answer},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def submit_feedback(candidate_id: int, confidence_score: int) -> dict:
    """
    Send the final feedback score to the backend.

    Parameters:

    * candidate_id: Candidate id for the completed interview
    * confidence_score: Final confidence score selected by the user

    Returns:

    * dict: JSON response from the backend

    Steps:

    1. Build the feedback payload
    2. Send it to the feedback endpoint
    3. Return the parsed JSON response
    """
    payload = {
        "candidate_id": candidate_id,
        "confidence_score": confidence_score,
    }
    response = requests.post(f"{BACKEND_URL}/submit-feedback", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def extract_preview_lines(extracted_text: str, line_count: int = 5) -> str:
    """
    Build a short preview from extracted resume text.

    Parameters:

    * extracted_text: Full text extracted from the resume
    * line_count: Number of non-empty lines to keep

    Returns:

    * str: Small preview text or a fallback message

    Steps:

    1. Split the text into lines
    2. Remove empty lines
    3. Return the first few readable lines
    """
    lines = [line.strip() for line in extracted_text.splitlines() if line.strip()]
    if not lines:
        return "No readable text was extracted from the resume."
    return "\n".join(lines[:line_count])


def format_backend_error(detail) -> str:
    """
    Convert backend validation details into a friendly message.

    Parameters:

    * detail: Error detail returned by the backend

    Returns:

    * str: Human-readable error message

    Steps:

    1. Handle plain string errors directly
    2. Convert field-based validation errors into readable lines
    3. Return a default message when the format is unknown
    """
    if isinstance(detail, str):
        return detail

    if isinstance(detail, list):
        messages = []
        for item in detail:
            if not isinstance(item, dict):
                messages.append(str(item))
                continue

            location_parts = item.get("loc", [])
            field_name = next((part for part in reversed(location_parts) if isinstance(part, str)), "field")
            field_label = FIELD_LABELS.get(field_name, field_name.replace("_", " ").title())
            message = item.get("msg", "Invalid value")
            messages.append(f"{field_label}: {message}")

        if messages:
            return "\n".join(messages)

    return "Request failed. Please check your input and try again."


def render_interview_questions(candidate_id: int) -> None:
    """
    Render one conversational interview question at a time.

    Parameters:

    * candidate_id: Candidate id tied to the current interview

    Returns:

    * None

    Steps:

    1. Show one active question
    2. Save one answer per submit
    3. Fetch and render the next question until complete
    """
    current_question = st.session_state.current_question_text
    total_questions = int(st.session_state.total_questions)
    current_number = int(st.session_state.current_question_number)

    if not current_question:
        st.info("No interview questions are available for this submission.")
        return

    st.subheader("AI Conversational Interview")
    st.caption("Answer each question and submit to continue to the next one.")
    st.progress(current_number / max(total_questions, 1))
    st.markdown(f"**Question {current_number} of {total_questions}**")
    st.markdown(current_question)

    history = st.session_state.interview_history
    if history:
        with st.expander("Show previous answers", expanded=False):
            for idx, item in enumerate(history, start=1):
                st.markdown(f"**Q{idx}. {item['question']}**")
                st.write(item["answer"])

    with st.form("interview_step_form"):
        answer = st.text_area(
            label="Your answer",
            key=f"answer_for_{current_number}",
            placeholder="Type your answer here...",
            height=120,
        )
        submitted_answer = st.form_submit_button("Submit & Next")

    if submitted_answer:
        clean_answer = answer.strip()
        if not clean_answer:
            st.warning("Please enter an answer before moving to the next question.")
            return

        try:
            with st.spinner("Saving your response and fetching next question..."):
                next_payload = submit_interview_answer_step(
                    candidate_id=candidate_id,
                    answer=clean_answer,
                )

            st.session_state.interview_history.append(
                {
                    "question": current_question,
                    "answer": clean_answer,
                }
            )

            progress = next_payload.get("data", {})
            if progress.get("completed"):
                st.success("Interview completed successfully.")
                st.session_state.feedback_candidate_id = candidate_id
                st.session_state.current_question_text = None
                st.session_state.current_question_number = 0
                st.session_state.total_questions = 0
                st.rerun()
            else:
                st.session_state.current_question_text = progress.get("question")
                st.session_state.current_question_number = int(progress.get("current_question_number", 1))
                st.session_state.total_questions = int(progress.get("total_questions", 0))
                st.success("Answer saved. Next question loaded.")
                st.rerun()
        except requests.HTTPError as error:
            error_detail = "Could not save responses."
            if error.response is not None:
                try:
                    error_payload = error.response.json()
                    error_detail = format_backend_error(error_payload.get("detail", error_detail))
                except ValueError:
                    error_detail = error.response.text or error_detail
            st.error(f"Backend error: {error_detail}")
        except requests.RequestException:
            st.error("Could not connect to the backend while saving answers.")


def render_feedback_form(candidate_id: int) -> None:
    """
    Render the final feedback form in the Streamlit app.

    Parameters:

    * candidate_id: Candidate id for the current interview flow

    Returns:

    * None

    Steps:

    1. Show a confidence score slider
    2. Wait for the user to submit feedback
    3. Send the feedback to the backend and show the result
    """
    st.subheader("Interview Feedback")
    st.caption("Share a quick final rating before finishing the process.")

    with st.form("feedback_form"):
        confidence_score = st.slider("Confidence Score", min_value=1, max_value=10, value=7)
        submitted_feedback = st.form_submit_button("Submit Feedback")

    if submitted_feedback:
        try:
            with st.spinner("Saving feedback and sending email..."):
                feedback_response = submit_feedback(
                    candidate_id=candidate_id,
                    confidence_score=confidence_score,
                )

            email_sent = feedback_response["data"].get("email_sent", False)
            if email_sent:
                st.success("Feedback submitted and email sent successfully.")
            else:
                st.success("Feedback submitted successfully.")
                st.warning(feedback_response["data"].get("email_error", "Email could not be sent."))

            st.session_state.feedback_candidate_id = None
        except requests.HTTPError as error:
            error_detail = "Could not save feedback."
            if error.response is not None:
                try:
                    error_payload = error.response.json()
                    error_detail = format_backend_error(error_payload.get("detail", error_detail))
                except ValueError:
                    error_detail = error.response.text or error_detail
            st.error(f"Backend error: {error_detail}")
        except requests.RequestException:
            st.error("Could not connect to the backend while saving feedback.")


st.set_page_config(page_title="TalentScout - AI Hiring Assistant", page_icon="🧭", layout="centered")

if "current_candidate_id" not in st.session_state:
    st.session_state.current_candidate_id = None
if "feedback_candidate_id" not in st.session_state:
    st.session_state.feedback_candidate_id = None
if "current_question_text" not in st.session_state:
    st.session_state.current_question_text = None
if "current_question_number" not in st.session_state:
    st.session_state.current_question_number = 0
if "total_questions" not in st.session_state:
    st.session_state.total_questions = 0
if "interview_history" not in st.session_state:
    st.session_state.interview_history = []

st.title("TalentScout - AI Hiring Assistant")
st.write("Submit candidate details and upload a resume to send data to the FastAPI backend.")

st.divider()

st.subheader("Candidate Details")

with st.form("candidate_form"):
    name = st.text_input("Name", placeholder="Asha Khan")
    email = st.text_input("Email", placeholder="asha@example.com")
    phone = st.text_input("Phone", placeholder="9876543210")
    job_role = st.radio("Job Role", options=JOB_ROLE_OPTIONS, horizontal=True)
    resume_file = st.file_uploader("Resume PDF", type=["pdf"])

    submitted = st.form_submit_button("Submit")


if submitted:
    if not name or not email:
        st.error("Please fill in Name and Email.")
    elif resume_file is None:
        st.error("Please upload a PDF resume before submitting.")
    elif phone.strip() and (not phone.strip().isdigit() or len(phone.strip()) != 10):
        st.error("Phone must contain exactly 10 digits.")
    else:
        candidate_payload = {
            "name": name.strip(),
            "email": email.strip(),
            "phone": phone.strip(),
            "job_role": job_role.strip(),
        }

        try:
            with st.spinner("Sending candidate data and uploading resume..."):
                candidate_response = submit_candidate(candidate_payload)
                candidate_id = int(candidate_response["data"]["id"])
                upload_resume(resume_file, candidate_id, job_role.strip())
                next_question_payload = get_next_interview_question(candidate_id)

            next_question_data = next_question_payload.get("data", {})

            st.session_state.current_candidate_id = candidate_id
            st.session_state.interview_history = []
            st.session_state.current_question_text = next_question_data.get("question")
            st.session_state.current_question_number = int(next_question_data.get("current_question_number", 1))
            st.session_state.total_questions = int(next_question_data.get("total_questions", 0))

            st.success("Candidate submitted and resume uploaded successfully.")

        except requests.HTTPError as error:
            error_detail = "Request failed."
            if error.response is not None:
                try:
                    error_payload = error.response.json()
                    error_detail = format_backend_error(error_payload.get("detail", error_detail))
                except ValueError:
                    error_detail = error.response.text or error_detail
            st.error(f"Backend error: {error_detail}")
        except requests.RequestException:
            st.error("Could not connect to the backend. Make sure FastAPI is running on http://127.0.0.1:8000.")

if st.session_state.current_candidate_id and st.session_state.current_question_text:
    render_interview_questions(
        candidate_id=int(st.session_state.current_candidate_id),
    )

if st.session_state.feedback_candidate_id:
    render_feedback_form(candidate_id=int(st.session_state.feedback_candidate_id))

st.divider()
