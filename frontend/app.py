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


def render_interview_questions(candidate_id: int, questions: list[str]) -> None:
    """
    Render the interview question form in the Streamlit app.

    Parameters:

    * candidate_id: Candidate id tied to the current interview
    * questions: List of questions generated by the backend

    Returns:

    * None

    Steps:

    1. Show the questions on the page
    2. Collect answers from the user
    3. Validate answers and send them to the backend
    """
    if not questions:
        st.info("No interview questions were generated for this submission.")
        return

    st.subheader("AI-Generated Interview Questions")
    st.caption("Answer each question below, then submit your responses.")

    with st.form("interview_answers_form"):
        answers: list[str] = []
        for index, question in enumerate(questions, start=1):
            st.markdown(f"**Q{index}. {question}**")
            answer = st.text_area(
                label=f"Your answer for Q{index}",
                key=f"interview_answer_{index}",
                placeholder="Type your answer here...",
                height=110,
                label_visibility="collapsed",
            )
            answers.append(answer.strip())

        submitted_answers = st.form_submit_button("Submit Answers")

    if submitted_answers:
        unanswered = [str(i) for i, answer in enumerate(answers, start=1) if not answer]
        if unanswered:
            st.warning(f"Please answer all questions. Missing: {', '.join(unanswered)}")
            return

        response_payload = [
            {
                "question": question,
                "answer": answer,
            }
            for question, answer in zip(questions, answers)
        ]

        try:
            with st.spinner("Saving your interview responses..."):
                submit_interview_answers(
                    candidate_id=candidate_id,
                    responses=response_payload,
                )
            st.success(f"Your interview responses were submitted successfully.")
            st.session_state.feedback_candidate_id = candidate_id
            st.session_state.current_interview_questions = []
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
if "current_interview_questions" not in st.session_state:
    st.session_state.current_interview_questions = []
if "feedback_candidate_id" not in st.session_state:
    st.session_state.feedback_candidate_id = None

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
                resume_response = upload_resume(resume_file, candidate_id, job_role.strip())

            interview_questions = resume_response["data"].get("interview_questions", [])

            st.session_state.current_candidate_id = candidate_id
            st.session_state.current_interview_questions = interview_questions

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

if st.session_state.current_candidate_id and st.session_state.current_interview_questions:
    render_interview_questions(
        candidate_id=int(st.session_state.current_candidate_id),
        questions=st.session_state.current_interview_questions,
    )

if st.session_state.feedback_candidate_id:
    render_feedback_form(candidate_id=int(st.session_state.feedback_candidate_id))

st.divider()