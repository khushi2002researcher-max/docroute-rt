from dotenv import load_dotenv
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional
from pathlib import Path

# Load .env only locally
if os.getenv("RENDER") is None:
    load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("SMTP_FROM")


def send_reminder_email(
    to: str,
    subject: str,
    text_body: str,
    html_body: Optional[str] = None,
    pdf_path: Optional[str] = None,
):
    if not SMTP_USERNAME or not SMTP_PASSWORD or not FROM_EMAIL:
        raise RuntimeError("SMTP credentials not configured")

    msg = EmailMessage()
    msg["From"] = FROM_EMAIL
    msg["To"] = to
    msg["Subject"] = subject

    msg.set_content(text_body)

    if html_body:
        msg.add_alternative(html_body, subtype="html")

    if pdf_path and Path(pdf_path).exists():
        with open(pdf_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="pdf",
                filename=Path(pdf_path).name,
            )

    context = ssl.create_default_context()

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
        server.ehlo()
        server.starttls(context=context)
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)


def send_email(to: str, subject: str, body: str):
    send_reminder_email(
        to=to,
        subject=subject,
        text_body=body,
    )
