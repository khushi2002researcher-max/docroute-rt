import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Optional
from datetime import datetime

from app.ai_routing.reminder_engine import mark_reminder_sent


SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

FROM_EMAIL = os.getenv(
    "FROM_EMAIL",
    "DocRoute <khushi2002researcher@gmail.com>",
)


# ======================================================
# EMAIL SENDER (CORE)
# ======================================================

def send_email(
    to: str,
    subject: str,
    text_body: str,
    html_body: Optional[str] = None,
    attachment_path: Optional[str] = None,
):
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        raise RuntimeError("SMTP credentials not configured")

    msg = EmailMessage()
    msg["From"] = FROM_EMAIL
    msg["To"] = to
    msg["Subject"] = subject

    msg.set_content(text_body)

    if html_body:
        msg.add_alternative(html_body, subtype="html")

    # Attachment
    if attachment_path:
        path = Path(attachment_path)
        if path.exists():
            with open(path, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="application",
                    subtype="octet-stream",
                    filename=path.name,
                )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)


# ======================================================
# REMINDER WRAPPER
# ======================================================

def send_reminder(
    *,
    db,
    reminder,
    history,
    routing,
    deadline,
):
    days_left = (deadline.deadline_date - datetime.now().date()).days

    subject = f"⏰ Reminder: {routing.document_name} – {days_left} day(s) left"

    text_body = f"""
Document: {routing.document_name}
Deadline: {deadline.deadline_date}
Days remaining: {days_left}

Rule: {history.rule_text}
Priority: {deadline.priority}

Please take necessary action.
"""

    html_body = f"""
<html>
  <body style="font-family: Arial;">
    <h2>⏰ Document Reminder</h2>
    <p><b>Document:</b> {routing.document_name}</p>
    <p><b>Deadline:</b> {deadline.deadline_date}</p>
    <p><b>Days Remaining:</b> {days_left}</p>
    <p><b>Rule:</b> {history.rule_text}</p>
    <p><b>Priority:</b> {deadline.priority}</p>
    <hr>
    <p style="color:red;">Action required</p>
  </body>
</html>
"""

    send_email(
        to=history.recipient,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        attachment_path=routing.ai_file_path,
    )

    mark_reminder_sent(db, reminder, history)
