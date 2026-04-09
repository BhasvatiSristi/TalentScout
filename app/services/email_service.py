from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
import os
import smtplib
from email.message import EmailMessage


def send_email(to_email: str, subject: str, body: str) -> None:
    """Send an email using SMTP settings from environment variables."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587").strip())
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from = os.getenv("EMAIL_FROM", smtp_user).strip()

    if not smtp_user or not smtp_password:
        raise RuntimeError("SMTP credentials are missing. Set SMTP_USER and SMTP_PASSWORD.")

    message = EmailMessage()
    message["From"] = smtp_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(message)
    except Exception as exc:
        raise RuntimeError(f"Email could not be sent: {str(exc)}") from exc
