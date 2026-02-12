from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import date


from app.auth.models import OCRHistory, AIDocument
from app.document.D_models import Document, AuditLog
from app.ai_routing.models import (
    DocumentRouting,
    RoutingDeadline,
    ReminderHistory,
    ReminderStatus,
)


def total_documents(db: Session, user_id: int) -> int:
    return db.query(Document.id).filter(
        Document.owner_id == user_id
    ).count()

def ocr_processed(db: Session, user_id: int) -> int:
    return db.query(OCRHistory.id).filter(
        OCRHistory.user_id == user_id
    ).count()

def ai_analyzed(db: Session, user_id: int) -> int:
    return db.query(AIDocument.id).filter(
        AIDocument.user_id == user_id
    ).count()

def active_deadlines(db: Session, user_id: int) -> int:
    return db.query(RoutingDeadline.id).join(
        DocumentRouting
    ).filter(
        DocumentRouting.user_id == user_id,
        RoutingDeadline.deadline_date >= date.today(),
    ).count()

def missed_deadlines(db: Session, user_id: int) -> int:
    return db.query(RoutingDeadline.id).join(
        DocumentRouting
    ).filter(
        DocumentRouting.user_id == user_id,
        RoutingDeadline.deadline_date < date.today(),
    ).count()

def document_lifecycle(db: Session, user_id: int):
    return db.query(
        func.date(Document.created_at).label("date"),
        func.count(Document.id).label("value"),
    ).filter(
        Document.owner_id == user_id
    ).group_by(
        func.date(Document.created_at)
    ).order_by(
        func.date(Document.created_at)
    ).all()

def ocr_time_series(db: Session, user_id: int):
    return db.query(
        func.date(OCRHistory.created_at).label("date"),
        func.count(OCRHistory.id).label("value"),
    ).filter(
        OCRHistory.user_id == user_id
    ).group_by(
        func.date(OCRHistory.created_at)
    ).order_by(
        func.date(OCRHistory.created_at)
    ).all()

def routing_decisions(db: Session, user_id: int):
    decision_case = case(
        (DocumentRouting.requires_human.is_(True), "HUMAN_REVIEW"),
        else_="AI_APPROVED",
    )

    return db.query(
        decision_case.label("label"),
        func.count(DocumentRouting.id).label("value"),
    ).filter(
        DocumentRouting.user_id == user_id
    ).group_by(
        decision_case
    ).all()

def deadlines_by_priority(db: Session, user_id: int):
    return db.query(
        RoutingDeadline.priority.label("priority"),
        func.count(RoutingDeadline.id).label("count"),
    ).join(
        DocumentRouting
    ).filter(
        DocumentRouting.user_id == user_id
    ).group_by(
        RoutingDeadline.priority
    ).all()

def reminders_by_status(db: Session, user_id: int):
    return db.query(
        ReminderHistory.status.label("status"),
        func.count(ReminderHistory.id).label("count"),
    ).join(
        DocumentRouting,
        ReminderHistory.routing_id == DocumentRouting.id
    ).filter(
        DocumentRouting.user_id == user_id
    ).group_by(
        ReminderHistory.status
    ).all()

def failed_reminders_today(db: Session, user_id: int) -> int:
    return db.query(ReminderHistory.id).join(
        DocumentRouting,
        ReminderHistory.routing_id == DocumentRouting.id
    ).filter(
        DocumentRouting.user_id == user_id,
        ReminderHistory.status == ReminderStatus.FAILED,
        ReminderHistory.sent_on == date.today(),
    ).count()

def latest_audit_logs(db: Session, user_id: int, limit: int = 50):
    return db.query(AuditLog).filter(
        AuditLog.performed_by == user_id
    ).order_by(
        AuditLog.created_at.desc()
    ).limit(limit).all()
