import requests
import streamlit as st


BACKEND_URL = "http://127.0.0.1:8000"

FIELD_LABELS = {
    "name": "Name",
    "email": "Email",
    "phone": "Phone",
    "job_role": "Job Role",
    "file": "Resume",
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
    response = requests.post(f"{BACKEND_URL}/candidates/intake", json=candidate_data, timeout=30)
    response.raise_for_status()
    return response.json()


def upload_resume(resume_file, job_role: str) -> dict:
    files = {
        "file": (
            resume_file.name,
            resume_file.getvalue(),
            resume_file.type or "application/pdf",
        )
    }
    data = {"job_role": job_role}
    response = requests.post(
        f"{BACKEND_URL}/candidates/resume/upload",
        data=data,
        files=files,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def extract_preview_lines(extracted_text: str, line_count: int = 5) -> str:
    lines = [line.strip() for line in extracted_text.splitlines() if line.strip()]
    if not lines:
        return "No readable text was extracted from the resume."
    return "\n".join(lines[:line_count])


def format_backend_error(detail) -> str:
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


st.set_page_config(page_title="TalentScout - AI Hiring Assistant", page_icon="🧭", layout="centered")

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
                resume_response = upload_resume(resume_file, job_role.strip())

            extracted_text = resume_response["data"]["extracted_text"]
            preview_text = extract_preview_lines(extracted_text)

            st.success("Candidate submitted and resume uploaded successfully.")

            st.subheader("Candidate API Response")
            st.json(candidate_response)

            st.subheader("Resume Upload Response")
            st.json(resume_response)

            st.subheader("Extracted Text Preview")
            st.text(preview_text)

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

st.divider()