from pydantic import BaseModel
from typing import List, Dict
from datetime import date, datetime
from typing import Dict, Any

# =========================
# TIME SERIES
# =========================

class TimeSeriesPoint(BaseModel):
    date: date
    value: int


class TimeSeriesResponse(BaseModel):
    label: str
    data: List[TimeSeriesPoint]


# =========================
# OVERVIEW KPI
# =========================

class OverviewKPIResponse(BaseModel):
    total_documents: int
    ocr_processed: int
    ai_analyzed: int
    active_deadlines: int
    pending_reminders: int
    missed_deadlines: int


# =========================
# WORKFLOW ANALYTICS
# =========================

class WorkflowRoutingItem(BaseModel):
    label: str
    value: int


class DeadlinePriorityItem(BaseModel):
    priority: str
    count: int


class WorkflowAnalyticsResponse(BaseModel):
    routing: List[WorkflowRoutingItem]
    deadlines: List[DeadlinePriorityItem]


# =========================
# AI ANALYTICS
# =========================

class AIAnalyticsResponse(BaseModel):
    chart: Dict[str, Any]


# =========================
# REMINDER ANALYTICS
# =========================

class ReminderStatusItem(BaseModel):
    status: str
    count: int


class ReminderAnalyticsResponse(BaseModel):
    data: List[ReminderStatusItem]
    failed_today: int


# =========================
# AUDIT LOGS
# =========================

class AuditLogItem(BaseModel):
    id: int
    action: str
    details: str | None
    performed_by: str
    created_at: datetime


class AuditLogResponse(BaseModel):
    logs: List[AuditLogItem]


# =========================
# SYSTEM HEALTH
# =========================

class ServiceStatusItem(BaseModel):
    service: str
    status: str


class SystemHealthResponse(BaseModel):
    services: List[ServiceStatusItem]


# =========================
# DOCUMENT CODE ANALYTICS ✅ REQUIRED
# =========================

class DocumentCodeAnalyticsResponse(BaseModel):
    sent_total: int
    received_total: int
    used_codes: int
    pending_codes: int
