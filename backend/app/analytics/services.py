from sqlalchemy.orm import Session
from app.doccode.models import DocumentCode
from app.analytics import queries, metrics

def get_overview_kpis(db: Session, user_id: int):
    total_docs = queries.total_documents(db, user_id)
    ocr_count = queries.ocr_processed(db, user_id)
    ai_count = queries.ai_analyzed(db, user_id)
    active = queries.active_deadlines(db, user_id)
    missed = queries.missed_deadlines(db, user_id)

    pending_reminders = max(active - missed, 0)

    return metrics.build_overview_kpis(
        total_documents=total_docs,
        ocr_processed=ocr_count,
        ai_analyzed=ai_count,
        active_deadlines=active,
        pending_reminders=pending_reminders,
        missed_deadlines=missed,
    )


def get_document_lifecycle(db: Session, user_id: int):
    rows = queries.document_lifecycle(db, user_id)
    return metrics.build_time_series("Document Uploads", rows)

def get_ocr_analytics(db: Session, user_id: int):
    rows = queries.ocr_time_series(db, user_id)
    return metrics.build_time_series("OCR Processed Files", rows)

def get_ai_analytics(db: Session, user_id: int):
    rows = queries.routing_decisions(db, user_id)

    return {
        "chart": {
            "label": "AI vs Human Decisions",
            "data": [
                {"label": label, "value": value}
                for label, value in rows
            ],
        }
    }

def get_workflow_analytics(db: Session, user_id: int):
    routing_rows = queries.routing_decisions(db, user_id)
    deadline_rows = queries.deadlines_by_priority(db, user_id)

    return metrics.build_workflow_analytics(
        routing_rows=routing_rows,
        deadline_rows=deadline_rows,
    )

def get_reminder_analytics(db: Session, user_id: int):
    status_rows = queries.reminders_by_status(db, user_id)
    failed_today = queries.failed_reminders_today(db, user_id)

    return metrics.build_reminder_analytics(
        status_rows=status_rows,
        failed_today=failed_today,
    )


def get_audit_live_feed(db: Session, user_id: int, limit: int = 50):
    logs = queries.latest_audit_logs(db, user_id, limit)
    return metrics.build_audit_logs(logs)

def get_system_health(db: Session):
    status_map = {
        "OCR Engine": True,
        "AI Engine": True,
        "Scheduler": True,
        "Email Service": True,
    }

    return metrics.build_system_health(status_map)


# =====================================================
# 📄 DOCUMENT CODE ANALYTICS (SENDER / RECEIVER)
# =====================================================

def get_doccode_analytics(db: Session, user_id: int):
    """
    Analytics for Document Code Exchange
    Used by Analytics Dashboard
    """

    sent_total = db.query(DocumentCode).filter(
        DocumentCode.owner_user_id == user_id
    ).count()

    received_total = db.query(DocumentCode).filter(
        DocumentCode.received_by_user_id == user_id
    ).count()

    used_codes = db.query(DocumentCode).filter(
        DocumentCode.owner_user_id == user_id,
        DocumentCode.is_used == True
    ).count()

    pending_codes = sent_total - used_codes

    return {
        "sent_total": sent_total,
        "received_total": received_total,
        "used_codes": used_codes,
        "pending_codes": max(pending_codes, 0),
    }
