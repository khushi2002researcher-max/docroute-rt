from datetime import datetime, date
import pytz
from sqlalchemy.orm import Session

from app.ai_routing.models import (
    ReminderHistory,
    RoutingReminder,
    ReminderStatus,
)
from app.ai_routing.reminder_sender import send_email
from app.ai_routing.reminder_engine import mark_reminder_sent
from app.database import SessionLocal


TIMEZONE = pytz.timezone("Asia/Kolkata")


def process_due_reminders():
    db: Session = SessionLocal()
    today = datetime.now(TIMEZONE).date()

    try:
        histories = (
            db.query(ReminderHistory)
            .join(RoutingReminder)
            .filter(
                ReminderHistory.status == ReminderStatus.PENDING,
                ReminderHistory.trigger_date <= today,
                RoutingReminder.active.is_(True),
            )
            .all()
        )

        for history in histories:
            reminder = history.reminder
            routing = reminder.routing
            deadline = reminder.deadline

            subject = f"⏰ Reminder: {routing.document_name}"

            text_body = f"""
Document: {routing.document_name}
Deadline: {deadline.deadline_date}
Days remaining: {history.days_remaining}
Priority: {deadline.priority}
Status: {routing.ai_flag}
"""

            html_body = f"""
<h2>⏰ Deadline Reminder</h2>
<p><b>Document:</b> {routing.document_name}</p>
<p><b>Deadline:</b> {deadline.deadline_date}</p>
<p><b>Days Remaining:</b> {history.days_remaining}</p>
<p><b>Priority:</b> {deadline.priority}</p>
<p><b>Status:</b> {routing.ai_flag}</p>
"""

            send_email(
                to=history.recipient,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
            )

            mark_reminder_sent(db, reminder, history)

    except Exception as e:
        db.rollback()
        raise e

    finally:
        db.close()
