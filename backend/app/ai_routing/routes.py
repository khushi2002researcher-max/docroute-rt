from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
)
from sqlalchemy.orm import Session
from uuid import uuid4
from typing import Optional
from pathlib import Path
import shutil
from datetime import datetime
import pytz

from app.ai_routing.reminder_engine import calculate_trigger_date
from app.ai_routing.scheduler import process_reminders

from app.ai_routing.models import DocumentCategory
from app.ai_routing.services import classify_document





from app.database import get_db
from app.auth.utils import get_current_user
from app.auth.models import User
from app.document.D_models import Document

from app.ai_routing.text_extractor import extract_text
from app.ai_routing.models import (
    DocumentRouting,
    RoutingDeadline,
    RoutingAuditLog,
    AIDecisionFlag,
    RoutingSource,
    AuditActor,
    PriorityLevel,
    RoutingReminder,
    ReminderHistory,
    RoutingEmailRecipient
    
)

from app.ai_routing.models import (
    ReminderUnit,
    ReminderDirection,
    ReminderChannel,
    ReminderStatus,
)

from app.ai_routing.schemas import (
    RoutingCreateResponse,
    AIAnalyzeRequest,
    AIAnalyzeResponse,
    RoutingHistoryResponse,
    HumanDeadlineCreate,
    ReminderCreate,
    ReminderHistoryUpdate,
   
)
from app.ai_routing.services import (
    calculate_ai_flag,
    calculate_priority,
    requires_human_review,
    extract_deadlines_from_text,
)

UPLOAD_DIR = Path("uploads/ai_routing")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/ai-routing", tags=["AI + Human Routing"])



# =====================================================
# DOCUMENTS (FOR DROPDOWN)
# =====================================================
@router.get("/documents/my")
def my_documents(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(Document).filter(Document.owner_id == user.id).all()


# =====================================================
# 1️⃣ CREATE ROUTING
# =====================================================
@router.post("/create", response_model=RoutingCreateResponse)
def create_routing(
    document_id: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not document_id and not file:
        raise HTTPException(400, "Either document_id or file is required")

    # ---------- EXISTING DOCUMENT ----------
    if document_id:
        document = (
            db.query(Document)
            .filter(Document.id == document_id, Document.owner_id == user.id)
            .first()
        )
        if not document:
            raise HTTPException(404, "Document not found")

        routing = DocumentRouting(
            routing_id=f"ROUTE-{uuid4().hex[:8].upper()}",
            user_id=user.id,
            document_id=document.id,
            document_name=document.file_name,
            file_type=document.file_type,
            source_type=RoutingSource.HUMAN,
            ai_flag=AIDecisionFlag.DATE_MISSING,
            confidence=None,
            requires_human=True,
        )

    # ---------- NEW FILE (AI) ----------
    else:
        if file.content_type not in (
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ):
            raise HTTPException(400, "Only PDF or DOCX allowed")

        file_id = f"{uuid4().hex}_{file.filename}"
        file_path = UPLOAD_DIR / file_id

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        routing = DocumentRouting(
            routing_id=f"ROUTE-{uuid4().hex[:8].upper()}",
            user_id=user.id,
            document_id=None,
            document_name=file.filename,
            file_type=file.content_type,
            ai_file_path=str(file_path),
            source_type=RoutingSource.AI,
            ai_flag=AIDecisionFlag.DATE_MISSING,
            confidence=None,
            requires_human=True,
        )

    db.add(routing)
    db.add(
        RoutingAuditLog(
            routing=routing,
            action="ROUTING_CREATED",
            details="Routing created",
            performed_by=AuditActor.SYSTEM,
        )
    )

    db.commit()
    db.refresh(routing)

    return routing


# =====================================================
# 2️⃣ AI ANALYSIS
# =====================================================

@router.post("/ai/analyze", response_model=AIAnalyzeResponse)
def analyze_with_ai(
    payload: AIAnalyzeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    routing = (
        db.query(DocumentRouting)
        .filter(
            DocumentRouting.routing_id == payload.routing_id,
            DocumentRouting.user_id == user.id,
        )
        .first()
    )
    if not routing:
        raise HTTPException(404, "Routing not found")

    # =================================================
    # ✅ CASE 1: AI FILE MISSING → HUMAN ROUTING
    # =================================================
    if not routing.ai_file_path:
        routing.ai_flag = AIDecisionFlag.DATE_MISSING
        routing.confidence = None
        routing.requires_human = True

        db.add(
            RoutingAuditLog(
                routing=routing,
                action="AI_ANALYSIS_SKIPPED",
                details="AI file missing, routed to human",
                performed_by=AuditActor.AI,
            )
        )

        db.commit()

        return {
            "routing_id": routing.routing_id,
            "ai_flag": routing.ai_flag,
            "confidence": routing.confidence,
            "requires_human": routing.requires_human,
            "document_category": routing.document_category,  # ✅ ADD
            "detected_deadlines": [],
            "created_at": routing.created_at,
        }   


    file_path = Path(routing.ai_file_path)

    # =================================================
    # ✅ CASE 2: FILE PATH INVALID → HUMAN ROUTING
    # =================================================
    if not file_path.exists():
        routing.ai_flag = AIDecisionFlag.DATE_MISSING
        routing.confidence = None
        routing.requires_human = True

        db.add(
            RoutingAuditLog(
                routing=routing,
                action="AI_ANALYSIS_SKIPPED",
                details="AI file not found, routed to human",
                performed_by=AuditActor.AI,
            )
        )

        db.commit()

        return {
            "routing_id": routing.routing_id,
            "ai_flag": routing.ai_flag,
            "confidence": None,
            "requires_human": True,
            "detected_deadlines": [],
            "created_at": routing.created_at,
        }

    # =================================================
    # ✅ CASE 3: RUN AI EXTRACTION
    # =================================================
    text = extract_text(str(file_path), routing.file_type)
    # ===============================
# 📄 DOCUMENT TYPE CLASSIFICATION
# ===============================
    # 📄 DOCUMENT TYPE (AI sets ONLY if empty)
    if routing.document_category is None:
        routing.document_category = classify_document(text)
   


    extracted_deadlines = extract_deadlines_from_text(text)

    detected_deadlines = []
    detected_date = None
    confidence = None

    if extracted_deadlines:
        best = max(extracted_deadlines, key=lambda x: x["confidence"])
        detected_date = best["deadline_date"]
        confidence = best["confidence"]
        detected_deadlines.append(best)

        db.add(
            RoutingDeadline(
                routing=routing,
                source=RoutingSource.AI,
                label=best["label"],
                deadline_date=best["deadline_date"],
                confidence=best["confidence"],
                priority=calculate_priority(best["deadline_date"]),
                ai_flag=calculate_ai_flag(best["deadline_date"]),
            )
        )

    # =================================================
    # ✅ FINAL AI DECISION (FOUND / NOT FOUND)
    # =================================================
    routing.ai_flag = calculate_ai_flag(detected_date)
    routing.confidence = confidence
    routing.requires_human = requires_human_review(detected_date, confidence)

    db.add(
        RoutingAuditLog(
            routing=routing,
            action="AI_ANALYSIS_COMPLETED",
            details=f"confidence={confidence}",
            performed_by=AuditActor.AI,
        )
    )

    db.commit()

    return {
        "routing_id": routing.routing_id,
        "ai_flag": routing.ai_flag,
        "confidence": routing.confidence,
        "requires_human": routing.requires_human,
        "detected_deadlines": detected_deadlines,
        "created_at": routing.created_at,
    }

# =====================================================
# 4️⃣ HISTORY
# =====================================================
@router.get("/history", response_model=list[RoutingHistoryResponse])
def routing_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    routings = (
        db.query(DocumentRouting)
        .filter(DocumentRouting.user_id == user.id)
        .order_by(DocumentRouting.created_at.desc())
        .all()
    )

    results = []
    for r in routings:
        latest_deadline = (
            db.query(RoutingDeadline)
            .filter(RoutingDeadline.routing_id == r.id)
            .order_by(RoutingDeadline.created_at.desc())
            .first()
        )

        results.append({
            "id": r.id,
            "routing_id": r.routing_id,
            "document_id": r.document_id,
            "document_name": r.document_name,
            "file_type": r.file_type,
            "document_category": r.document_category,
            "notes": r.notes,
            "source_type": r.source_type,
            "ai_flag": r.ai_flag,
            "confidence": r.confidence,
            "requires_human": r.requires_human,
            "created_at": r.created_at,
            # ✅ THIS IS THE KEY ADDITION
            "deadline_date": latest_deadline.deadline_date if latest_deadline else None,
        })

    return results

# =====================================================
# 3️⃣ HUMAN DEADLINE CREATE
# =====================================================
def flag_from_priority(priority: PriorityLevel) -> AIDecisionFlag:
    if priority == PriorityLevel.CRITICAL:
        return AIDecisionFlag.DEADLINE_CRITICAL
    if priority == PriorityLevel.HIGH:
        return AIDecisionFlag.DEADLINE_NEAR
    return AIDecisionFlag.DEADLINE_FOUND

@router.post("/human/deadline")
def create_human_deadline(
    payload: HumanDeadlineCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    routing = (
        db.query(DocumentRouting)
        .filter(
            DocumentRouting.routing_id == payload.routing_id,
            DocumentRouting.user_id == user.id,
        )
        .first()
    )

    if not routing:
        raise HTTPException(404, "Routing not found")

# ✅ Manual document type always wins
    if payload.document_category:
        routing.document_category = payload.document_category

    # ===============================
    # 🗓️ CREATE DEADLINE
    # ===============================
    flag = flag_from_priority(payload.priority)

    deadline = RoutingDeadline(
        routing=routing,
        source=RoutingSource.HUMAN,
        label=payload.label,
        deadline_date=payload.deadline_date,
        confidence=1.0,
        priority=payload.priority,
        ai_flag=flag,
    )
    db.add(deadline)
    db.flush() 

    routing.notes = payload.notes
    routing.ai_flag = flag
    routing.confidence = 1.0
    routing.requires_human = False

    # ===============================
    # 🔔 DEFAULT REMINDER (0 DAY BEFORE)
    # ===============================
    # ===============================
# 🔔 DEFAULT REMINDER (ONLY ONE)
# ===============================
    default_reminder = (
        db.query(RoutingReminder)
        .filter(
            RoutingReminder.routing_id == routing.id,
            RoutingReminder.trigger_value == 0,
            RoutingReminder.trigger_unit == ReminderUnit.DAY,
            RoutingReminder.direction == ReminderDirection.BEFORE,
            RoutingReminder.active.is_(True),
        )
        .first()
    )

# ➕ Create ONLY if not exists
    if not default_reminder:
        default_reminder = RoutingReminder(
            routing_id=routing.id,
            deadline_id=deadline.id,
            trigger_value=0,
            trigger_unit=ReminderUnit.DAY,
            direction=ReminderDirection.BEFORE,
            channel=ReminderChannel.EMAIL,
            active=True,
        )
        db.add(default_reminder)
        db.flush()
    else:
    # 🔁 Update deadline link if editing
        default_reminder.deadline_id = deadline.id


    # ===============================
    # 🧾 REMINDER HISTORY
    # ===============================
    from datetime import date
    today = date.today()

   # 🔁 UPDATE EXISTING PENDING HISTORY RECIPIENTS
    recipients = [user.email] + (payload.cc_emails or [])

    recipient_str = ", ".join(sorted(set(recipients)))

    db.query(ReminderHistory).filter(
        ReminderHistory.routing_id == routing.id,
        ReminderHistory.status == ReminderStatus.PENDING,
    ).update(
        {"recipient": recipient_str},
        synchronize_session=False,
    )


    
    today = date.today()

    existing_history = (
        db.query(ReminderHistory)
        .filter(
            ReminderHistory.reminder_id == default_reminder.id,
            ReminderHistory.status == ReminderStatus.PENDING,
        )
        .first()
    )

    if existing_history:
        existing_history.submitted_on = payload.deadline_date
        existing_history.trigger_date = payload.deadline_date
        existing_history.days_remaining = max(
            (payload.deadline_date - today).days, 0
        )
        existing_history.recipient = recipient_str
    else:
        history = ReminderHistory(
            reminder_id=default_reminder.id,
            routing_id=routing.id,
            rule_text="0 day before",
            submitted_on=payload.deadline_date,
            trigger_date=payload.deadline_date,
            days_remaining=max(
                (payload.deadline_date - today).days, 0
            ),
            status=ReminderStatus.PENDING,
            recipient=recipient_str,
            channel=ReminderChannel.EMAIL,
        )
        db.add(history)



    # ===============================
    # 🧾 AUDIT
    # ===============================
    db.add(
        RoutingAuditLog(
            routing=routing,
            action="HUMAN_DEADLINE_ADDED",
            details=f"deadline={payload.deadline_date}, notes={payload.notes}",
            performed_by=AuditActor.HUMAN,
        )
    )

    # ===============================
    # 📧 CC EMAILS
    # ===============================
    routing.email_recipients.clear()
    for email in payload.cc_emails:
        routing.email_recipients.append(
            RoutingEmailRecipient(
                routing_id=routing.id,
                email=email,
            )
        )

    db.commit()

    # ===============================
    # 🚀 IMMEDIATE SEND IF TODAY
    # ===============================
    if payload.email_enabled and payload.deadline_date == today:
        process_reminders()

        

    return {
        "message": "Human deadline saved",
        "routing_id": routing.routing_id,
    }




# =====================================================
# 🔔 GET REMINDERS FOR A ROUTING
# =====================================================
@router.get("/reminders/{routing_id}")
def get_reminders(
    routing_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    routing = (
        db.query(DocumentRouting)
        .filter(
            DocumentRouting.routing_id == routing_id,
            DocumentRouting.user_id == user.id,
        )
        .first()
    )
    if not routing:
        raise HTTPException(404, "Routing not found")

    reminders = (
        db.query(RoutingReminder)
        .filter(
            RoutingReminder.routing_id == routing.id,
            RoutingReminder.active.is_(True),
        )
        .order_by(RoutingReminder.created_at.desc())
        .all()
    )

    return reminders


@router.post("/reminders")
def create_reminder(
    payload: ReminderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    routing = db.query(DocumentRouting).filter(
        DocumentRouting.routing_id == payload.routing_id,
        DocumentRouting.user_id == user.id,
    ).first()
    if not routing:
        raise HTTPException(404, "Routing not found")

    deadline = (
        db.query(RoutingDeadline)
        .filter(RoutingDeadline.routing_id == routing.id)
        .order_by(RoutingDeadline.created_at.desc())
        .first()
    )
    if not deadline:
        raise HTTPException(400, "No deadline found")

    # ✅ CREATE REMINDER
    reminder = RoutingReminder(
        routing_id=routing.id,
        deadline_id=deadline.id,
        trigger_value=payload.trigger_value,
        trigger_unit=payload.trigger_unit,
        direction=payload.direction,
        channel=payload.channel,
        active=True,
    )

    db.add(reminder)
    db.flush()  # get reminder.id

    # =====================================================
    # ✅ DATE-ONLY TRIGGER (DEFINE IT!)
    # =====================================================
    trigger_date = calculate_trigger_date(
        deadline_date=deadline.deadline_date,
        trigger_value=payload.trigger_value,
        trigger_unit=payload.trigger_unit,
        direction=payload.direction,
    )

    today = datetime.now(pytz.timezone("Asia/Kolkata")).date()
    days_remaining = (trigger_date - today).days

    if days_remaining < 0:
        days_remaining = 0

    # =====================================================
    # ✅ EMAIL RECIPIENTS
    # =====================================================
    recipients = [user.email]

    ccs = (
        db.query(RoutingEmailRecipient)
        .filter(RoutingEmailRecipient.routing_id == routing.id)
        .all()
    )
    recipients.extend([c.email for c in ccs])
    recipient_str = ", ".join(sorted(set(recipients)))

    # =====================================================
    # ✅ HISTORY (DATE ONLY — NO trigger_at)
    # =====================================================
    history = ReminderHistory(
    reminder_id=reminder.id,
    routing_id=routing.id,
    rule_text=(
        f"{payload.trigger_value or 0} "
        f"{payload.trigger_unit.value.lower()} "
        f"{payload.direction.value.lower() if payload.direction else ''}"
    ),
    submitted_on=deadline.deadline_date,
    trigger_date=trigger_date,
    days_remaining=days_remaining,
    status=ReminderStatus.PENDING,
    recipient=recipient_str,
    channel=payload.channel,
)


    db.add(history)

    db.add(
        RoutingAuditLog(
            routing_id=routing.id,
            action="REMINDER_CREATED",
            details=history.rule_text,
            performed_by=AuditActor.HUMAN,
        )
    )

    db.commit()

# 🚀 IMMEDIATE TRIGGER IF DATE MATCHES
    today = datetime.now(pytz.timezone("Asia/Kolkata")).date()
    if trigger_date == today:
        process_reminders()



    return {"message": "Reminder created"}



@router.put("/reminders/{reminder_id}")
def update_reminder(
    reminder_id: int,
    payload: ReminderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    reminder = (
        db.query(RoutingReminder)
        .join(DocumentRouting)
        .filter(
            RoutingReminder.id == reminder_id,
            DocumentRouting.user_id == user.id,
        )
        .first()
    )

    if not reminder:
        raise HTTPException(404, "Reminder not found")

    reminder.trigger_value = payload.trigger_value
    reminder.trigger_unit = payload.trigger_unit
    reminder.direction = payload.direction
    reminder.channel = payload.channel

    # 🔁 Update only future (pending) history rows
    db.query(ReminderHistory).filter(
        ReminderHistory.reminder_id == reminder.id,
        ReminderHistory.status == ReminderStatus.PENDING

,
    ).update(
        {
            "rule_text": f"{payload.trigger_value} "
                         f"{payload.trigger_unit.value.lower()} "
                         f"{payload.direction.value.lower()}",
        },
        synchronize_session=False,
    )

    db.add(
        RoutingAuditLog(
            routing=reminder.routing,
            action="REMINDER_UPDATED",
            details=f"reminder_id={reminder.id}",
            performed_by=AuditActor.HUMAN,
        )
    )

    db.commit()
    return {"message": "Reminder updated successfully"}

@router.delete("/reminders/{reminder_id}")
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    reminder = (
        db.query(RoutingReminder)
        .join(DocumentRouting)
        .filter(
            RoutingReminder.id == reminder_id,
            DocumentRouting.user_id == user.id,
        )
        .first()
    )

    if not reminder:
        raise HTTPException(404, "Reminder not found")

    # 🔕 Deactivate reminder
    reminder.active = False

    # ⏭ Mark pending history as SKIPPED
    db.query(ReminderHistory).filter(
        ReminderHistory.reminder_id == reminder.id,
        ReminderHistory.status == ReminderStatus.PENDING

,
    ).update(
        {"status": ReminderStatus.SKIPPED}
,
        synchronize_session=False,
    )

    db.add(
        RoutingAuditLog(
            routing=reminder.routing,
            action="REMINDER_DELETED",
            details=f"reminder_id={reminder.id}",
            performed_by=AuditActor.HUMAN,
        )
    )

    db.commit()
    return {"message": "Reminder deleted"}


@router.get("/reminders/history/{routing_id}")
def reminder_history(
    routing_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    routing = db.query(DocumentRouting).filter(
        DocumentRouting.routing_id == routing_id,
        DocumentRouting.user_id == user.id,
    ).first()

    if not routing:
        raise HTTPException(404, "Routing not found")

    history = (
        db.query(ReminderHistory)
        .filter(ReminderHistory.routing_id == routing.id)
        .order_by(ReminderHistory.trigger_date.desc())

        .all()
    )
    from datetime import date
    today = date.today()


    return [
    {
        "id": h.id,
        "rule_text": h.rule_text,
        "submitted_on": h.submitted_on,
        "trigger_date": h.trigger_date,

        # ✅ FIX: calculate live
        "days_remaining": max(
            (h.trigger_date - today).days,
            0
        ),

        "status": h.status,
        "recipient": h.recipient,
        "channel": h.channel,
    }
    for h in history
    ]



@router.delete("/reminders/history/{history_id}")
def delete_reminder_history(
    history_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    history = (
        db.query(ReminderHistory)
        .join(DocumentRouting, ReminderHistory.routing_id == DocumentRouting.id)
        .filter(
            ReminderHistory.id == history_id,
            DocumentRouting.user_id == user.id,
        )
        .first()
    )

    if not history:
        raise HTTPException(404, "Reminder history not found")

    db.delete(history)

    db.add(
        RoutingAuditLog(
            routing_id=history.routing_id,
            action="REMINDER_HISTORY_DELETED",
            details=f"history_id={history_id}",
            performed_by=AuditActor.HUMAN,
        )
    )

    db.commit()
    return {"message": "Reminder history deleted"}



@router.delete("/{routing_id}")
def delete_routing(
    routing_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    routing = db.query(DocumentRouting).filter(
        DocumentRouting.routing_id == routing_id,
        DocumentRouting.user_id == user.id,
    ).first()

    if not routing:
        raise HTTPException(404, "Routing not found")

    db.delete(routing)
    db.commit()

    return {"message": "Routing deleted"}



