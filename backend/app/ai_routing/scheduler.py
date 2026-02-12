from datetime import datetime
import pytz

from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
import logging

from app.auth.models import User
from app.database import SessionLocal
from app.ai_routing.models import (
    RoutingReminder,
    ReminderHistory,
    ReminderStatus,
    RoutingEmailRecipient,
)
from app.ai_routing.reminder_engine import calculate_trigger_date
from app.email import send_reminder_email

scheduler = BackgroundScheduler()
logger = logging.getLogger(__name__)


# =====================================================
# CORE REMINDER JOB
# =====================================================
def process_reminders():
    logger.warning("⏰ Scheduler tick running")
    db: Session = SessionLocal()
    today = datetime.now(pytz.timezone("Asia/Kolkata")).date()


    try:
        reminders = (
            db.query(RoutingReminder)
            .filter(RoutingReminder.active.is_(True))
            .all()
        )

        for reminder in reminders:
            deadline = reminder.deadline
            routing = reminder.routing

            if not deadline or not routing:
                continue

            # ===============================
            # 📧 COLLECT RECIPIENTS
            # ===============================
            recipients = []

            user = db.query(User).filter(User.id == routing.user_id).first()
            if user and user.email:
                recipients.append(user.email)

            ccs = (
                db.query(RoutingEmailRecipient)
                .filter(RoutingEmailRecipient.routing_id == routing.id)
                .all()
            )
            recipients.extend([c.email for c in ccs])

            recipients = sorted(set(recipients))
            if not recipients:
                continue

            recipient_str = ", ".join(recipients)

            # ===============================
            # 📅 TRIGGER DATE
            # ===============================
            trigger_date = calculate_trigger_date(
                deadline_date=deadline.deadline_date,
                trigger_value=reminder.trigger_value,
                trigger_unit=reminder.trigger_unit,
                direction=reminder.direction,
            )

            if today != trigger_date:
                continue

            # ===============================
            # 🔎 HISTORY ROW
            # ===============================
            history = (
                db.query(ReminderHistory)
                .filter(
                    ReminderHistory.reminder_id == reminder.id,
                    ReminderHistory.trigger_date == trigger_date,
                    ReminderHistory.status == ReminderStatus.PENDING,
                )
                .first()
            )

            if not history:
                continue

            days_to_deadline = (deadline.deadline_date - today).days

            # ===============================
            # 📝 NOTES BLOCK
            # ===============================
            notes_block = ""
            if routing.notes:
                notes_block = f"""
                <hr>
                <p><b>Notes:</b></p>
                <p>{routing.notes}</p>
                """

            # ===============================
            # 📧 EMAIL CONTENT
            # ===============================
            if days_to_deadline == 0:
                subject = f"🚨 CRITICAL: Deadline TODAY – {routing.routing_id}"
                html_body = f"""
                <h2 style="color:red">🚨 CRITICAL DEADLINE TODAY</h2>
                <p><b>Document:</b> {routing.document_name}</p>
                <p><b>Deadline:</b> {deadline.deadline_date}</p>
                <p style="color:red;font-weight:bold">
                    Immediate action is required.
                </p>
                {notes_block}
                """
            else:
                subject = f"⚠️ Reminder: Deadline in {days_to_deadline} Days – {routing.routing_id}"
                html_body = f"""
                <h3 style="color:orange">Upcoming Deadline</h3>
                <p><b>Document:</b> {routing.document_name}</p>
                <p><b>Deadline:</b> {deadline.deadline_date}</p>
                {notes_block}
                """

                        # ===============================
            # 📧 SEND EMAIL
            # ===============================
            try:
                text_notes = routing.notes if routing.notes else "—"

                send_reminder_email(
                    to=recipient_str,
                    subject=subject,
                    text_body=(
                        f"Document: {routing.document_name}\n"
                        f"Deadline: {deadline.deadline_date}\n\n"
                        f"Notes:\n{text_notes}"
                    ),
                    html_body=html_body,
                    attachment_path=routing.ai_file_path,

                )

                history.status = ReminderStatus.SENT
                history.sent_on = today
                history.days_remaining = max(days_to_deadline, 0)
                reminder.active = False

            except Exception:
                logger.exception("Email send failed")
                history.status = ReminderStatus.FAILED
                history.sent_on = today


        db.commit()

    except Exception:
        logger.exception("Reminder scheduler failed")
        db.rollback()

    finally:
        db.close()


# =====================================================
# SCHEDULER START
# =====================================================
def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            process_reminders,
            "interval",
            minutes=1,
            id="routing_reminder_job",
            replace_existing=True,
        )
        scheduler.start()
