from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
    Enum,
    Float,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.database import Base


# =====================================================
# ENUMS
# =====================================================

class RoutingSource(str, enum.Enum):
    AI = "AI"
    HUMAN = "HUMAN"


class DeadlineLabel(str, enum.Enum):
    SUBMISSION = "SUBMISSION"
    DUE = "DUE"
    EXPIRY = "EXPIRY"
    HEARING = "HEARING"
    RENEWAL = "RENEWAL"
    FILING = "FILING"
    VALID_TILL = "VALID_TILL"
    OTHER = "OTHER"


class PriorityLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AIDecisionFlag(str, enum.Enum):
    DEADLINE_FOUND = "DEADLINE_FOUND"
    DATE_AMBIGUOUS = "DATE_AMBIGUOUS"
    DATE_MISSING = "DATE_MISSING"
    DEADLINE_NEAR = "DEADLINE_NEAR"
    DEADLINE_CRITICAL = "DEADLINE_CRITICAL"
    MISSED_DEADLINE = "MISSED_DEADLINE"


class DocumentCategory(str, enum.Enum):
    SUBMISSION = "SUBMISSION"
    LEGAL = "LEGAL"
    AGREEMENT = "AGREEMENT"
    CONTRACT = "CONTRACT"
    INVOICE = "INVOICE"
    POLICY = "POLICY"
    NOTICE = "NOTICE"
    OTHER = "OTHER"



class AuditActor(str, enum.Enum):
    AI = "AI"
    HUMAN = "HUMAN"
    SYSTEM = "SYSTEM"


# ================= ENUMS =================

class ReminderUnit(str, enum.Enum):
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    EXACT = "EXACT"


class ReminderDirection(str, enum.Enum):
    BEFORE = "BEFORE"
    AFTER = "AFTER"


class ReminderChannel(str, enum.Enum):
    EMAIL = "EMAIL"

class ReminderStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


# =====================================================
# 📌 DOCUMENT ROUTING (MAIN TABLE)
# =====================================================

class DocumentRouting(Base):
    __tablename__ = "document_routings"

    id = Column(Integer, primary_key=True, index=True)
    routing_id = Column(String, unique=True, index=True, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    document_id = Column(Integer, nullable=True)  # optional link
    document_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)

    ai_file_path = Column(String, nullable=True)  # AI processed file only

    source_type = Column(Enum(RoutingSource, native_enum=False), nullable=False)
    ai_flag = Column(Enum(AIDecisionFlag, native_enum=False), nullable=False)

    confidence = Column(Float, nullable=True)
    requires_human = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True) 

    document_category = Column(Enum(DocumentCategory, native_enum=False), nullable=True)


    

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ✅ FIXED RELATIONSHIPS
    deadlines = relationship(
        "RoutingDeadline",
        back_populates="routing",
        cascade="all, delete-orphan",
    )

    email_recipients = relationship(
        "RoutingEmailRecipient",
        back_populates="routing",
        cascade="all, delete-orphan",
    )

    audits = relationship(
        "RoutingAuditLog",
        back_populates="routing",
        cascade="all, delete-orphan",
    )

    reminders = relationship(
    "RoutingReminder",
    back_populates="routing",
    cascade="all, delete-orphan",
)



# =====================================================
# ⏰ ROUTING DEADLINES
# =====================================================

class RoutingDeadline(Base):
    __tablename__ = "routing_deadlines"

    id = Column(Integer, primary_key=True)

    reminders = relationship(
        "RoutingReminder",
        back_populates="deadline",
        cascade="all, delete-orphan",
    )
    routing_id = Column(
        Integer,
        ForeignKey("document_routings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    


    source = Column(Enum(RoutingSource, native_enum=False), nullable=False)
    label = Column(Enum(DeadlineLabel,native_enum=False), nullable=False)

    deadline_date = Column(Date, nullable=False)

    confidence = Column(Float, nullable=True)

    priority = Column(
        Enum(PriorityLevel,native_enum=False),
        default=PriorityLevel.MEDIUM,
        nullable=False,
    )

    ai_flag = Column(Enum(AIDecisionFlag,native_enum=False), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    routing = relationship("DocumentRouting", back_populates="deadlines")


# =====================================================
# 📧 EMAIL RECIPIENTS
# =====================================================

class RoutingEmailRecipient(Base):
    __tablename__ = "routing_email_recipients"

    id = Column(Integer, primary_key=True)

    routing_id = Column(
        Integer,
        ForeignKey("document_routings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    email = Column(String(255), nullable=False)

    routing = relationship("DocumentRouting", back_populates="email_recipients")


# =====================================================
# 🧾 AUDIT LOG
# =====================================================

class RoutingAuditLog(Base):
    __tablename__ = "routing_audit_logs"

    id = Column(Integer, primary_key=True)

    routing_id = Column(
        Integer,
        ForeignKey("document_routings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    action = Column(String(150), nullable=False)
    details = Column(Text, nullable=True)

    performed_by = Column(Enum(AuditActor,native_enum=False), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    routing = relationship("DocumentRouting", back_populates="audits")



# ================= REMINDERS =================

class RoutingReminder(Base):
    __tablename__ = "routing_reminders"

    id = Column(Integer, primary_key=True)
    routing_id = Column(Integer, ForeignKey("document_routings.id", ondelete="CASCADE"),index=True)
    deadline_id = Column(Integer, ForeignKey("routing_deadlines.id", ondelete="CASCADE"),index=True)

    trigger_value = Column(Integer, nullable=True)
    trigger_unit = Column(Enum(ReminderUnit,native_enum=False), nullable=False)
    direction = Column(Enum(ReminderDirection,native_enum=False), nullable=True)

    trigger_date_override = Column(Date, nullable=True)


    channel = Column(Enum(ReminderChannel,native_enum=False), default=ReminderChannel.EMAIL)
    active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    routing = relationship("DocumentRouting", back_populates="reminders")
    deadline = relationship("RoutingDeadline")

    # ✅ ADD THIS
    history = relationship(
        "ReminderHistory",
        backref="reminder",
        cascade="all, delete-orphan",
    )

# ================= REMINDER HISTORY =================

class ReminderHistory(Base):
    __tablename__ = "routing_reminder_history"

    id = Column(Integer, primary_key=True)

    reminder_id = Column(Integer, ForeignKey("routing_reminders.id", ondelete="CASCADE"))
    routing_id = Column(Integer, ForeignKey("document_routings.id", ondelete="CASCADE"))

    rule_text = Column(String(200))

    # Deadline finalized date (AI or Human)
    submitted_on = Column(Date, nullable=False)

    trigger_date = Column(Date, nullable=False)
    sent_on = Column(Date, nullable=True)




    days_remaining = Column(Integer)
    status = Column(Enum(ReminderStatus,native_enum=False), nullable=False)
 # PENDING / SENT / FAILED / SKIPPED
    recipient = Column(String(255))
    channel = Column(Enum(ReminderChannel,native_enum=False), nullable=False)


    routing = relationship("DocumentRouting")

