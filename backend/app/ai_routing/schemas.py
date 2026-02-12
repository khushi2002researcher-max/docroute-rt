from pydantic import BaseModel, Field, EmailStr
from datetime import date, datetime
from typing import Optional, List
from enum import Enum

from app.ai_routing.models import (
    RoutingSource,
    DeadlineLabel,
    PriorityLevel,
    AIDecisionFlag,
    AuditActor,
    ReminderUnit,
    ReminderDirection,
    ReminderChannel,
    ReminderStatus,
    DocumentCategory, 

)

# =====================================================
# AI ANALYSIS REQUEST
# =====================================================

class AIAnalyzeRequest(BaseModel):
    routing_id: str


# =====================================================
# AI DETECTED DEADLINE
# =====================================================

class AIDetectedDeadline(BaseModel):
    deadline_date: date
    label: DeadlineLabel
    confidence: float = Field(..., ge=0.0, le=1.0)


# =====================================================
# AI ANALYSIS RESPONSE
# =====================================================

class AIAnalyzeResponse(BaseModel):
    routing_id: str
    ai_flag: AIDecisionFlag
    confidence: Optional[float]
    requires_human: bool
    document_category: Optional[DocumentCategory] = None
    detected_deadlines: List[AIDetectedDeadline] = Field(default_factory=list)
    created_at: datetime

    class Config:
        use_enum_values = True


# =====================================================
# ROUTING CREATE RESPONSE
# =====================================================

class RoutingCreateResponse(BaseModel):
    routing_id: str
    document_id: Optional[int]
    document_name: str
    file_type: str
    source_type: RoutingSource
    ai_flag: AIDecisionFlag
    confidence: Optional[float]
    requires_human: bool
    document_category: Optional[DocumentCategory] = None 
    created_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True


# =====================================================
# HUMAN DEADLINE CREATE
# =====================================================

class HumanDeadlineCreate(BaseModel):
    routing_id: str
    deadline_date: date
    label: DeadlineLabel = DeadlineLabel.SUBMISSION
    priority: PriorityLevel = PriorityLevel.MEDIUM
    cc_emails: list[EmailStr] = Field(default_factory=list)
    notes: Optional[str] = None
    email_enabled: bool = True
    document_category: Optional[DocumentCategory] = None



# =====================================================
# EMAIL RECIPIENT CREATE
# =====================================================

class EmailRecipientCreate(BaseModel):
    routing_id: str
    email: EmailStr


# =====================================================
# ROUTING DEADLINE RESPONSE
# =====================================================

class RoutingDeadlineResponse(BaseModel):
    id: int
    source: RoutingSource
    label: DeadlineLabel
    deadline_date: date
    confidence: Optional[float]
    priority: PriorityLevel
    ai_flag: AIDecisionFlag
    created_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True



# =====================================================
# ROUTING HISTORY RESPONSE
# =====================================================



class RoutingHistoryResponse(BaseModel):
    id: int
    routing_id: str
    document_id: Optional[int]
    document_name: str
    file_type: str

    # ✅ ADD THIS LINE
    deadline_date: Optional[date] = None

    document_category: Optional[DocumentCategory] = None
    notes: Optional[str] = None
    source_type: RoutingSource
    ai_flag: AIDecisionFlag
    confidence: Optional[float]
    requires_human: bool
    created_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True


# =====================================================
# EMAIL RECIPIENT RESPONSE
# =====================================================

class RoutingEmailRecipientResponse(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True
        use_enum_values = True


# =====================================================
# AUDIT LOG RESPONSE
# =====================================================

class RoutingAuditLogResponse(BaseModel):
    id: int
    action: str
    details: Optional[str]
    performed_by: AuditActor
    created_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True


# =====================================================
# REMINDER CREATE / UPDATE
# =====================================================

class ReminderCreate(BaseModel):
    routing_id: str
    trigger_value: Optional[int] = None
    trigger_unit: ReminderUnit
    direction: Optional[ReminderDirection] = None
    trigger_at_override: Optional[datetime] = None
    channel: ReminderChannel = ReminderChannel.EMAIL


class ReminderUpdate(BaseModel):
    trigger_value: Optional[int]
    trigger_unit: ReminderUnit
    direction: Optional[ReminderDirection]
    trigger_at_override: Optional[datetime]
    channel: ReminderChannel


# =====================================================
# REMINDER HISTORY RESPONSE
# =====================================================

class ReminderHistoryResponse(BaseModel):
    id: int
    rule_text: str
    submitted_on: date

    trigger_date: date          # ✅ FIXED (was trigger_at)
    sent_on: Optional[date]     # ✅ FIXED (was sent_at)

    days_remaining: int
    status: ReminderStatus
    recipient: str
    channel: ReminderChannel

    class Config:
        from_attributes = True
        use_enum_values = True


class ReminderHistoryUpdate(BaseModel):
    trigger_date: date