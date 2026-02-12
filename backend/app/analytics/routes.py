from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi import Query

from app.database import get_db
from app.auth.utils import get_current_user
from app.auth.models import User

from app.analytics.schemas import (
    OverviewKPIResponse,
    TimeSeriesResponse,
    WorkflowAnalyticsResponse,
    ReminderAnalyticsResponse,
    AuditLogResponse,
    SystemHealthResponse,
    AIAnalyticsResponse,
    DocumentCodeAnalyticsResponse
)

from app.analytics.services import (
    get_overview_kpis,
    get_document_lifecycle,
    get_ocr_analytics,
    get_ai_analytics,
    get_workflow_analytics,
    get_reminder_analytics,
    get_audit_live_feed,
    get_system_health,
    get_doccode_analytics,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=OverviewKPIResponse)
def analytics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_overview_kpis(db, current_user.id)


@router.get("/document-lifecycle", response_model=TimeSeriesResponse)
def document_lifecycle(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_document_lifecycle(db, current_user.id)


@router.get("/ocr", response_model=TimeSeriesResponse)
def ocr_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_ocr_analytics(db, current_user.id)


@router.get("/ai", response_model=AIAnalyticsResponse)
def ai_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_ai_analytics(db, current_user.id)


@router.get("/workflow", response_model=WorkflowAnalyticsResponse)
def workflow_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_workflow_analytics(db, current_user.id)


@router.get("/reminders", response_model=ReminderAnalyticsResponse)
def reminder_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_reminder_analytics(db, current_user.id)


@router.get("/audit-live", response_model=AuditLogResponse)
def audit_live_feed(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_audit_live_feed(db, current_user.id, limit)


@router.get("/system-health", response_model=SystemHealthResponse)
def system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_system_health(db)

# =====================================================
# 📄 DOCUMENT CODE ANALYTICS
# =====================================================
@router.get(
    "/doc-code",
    response_model=DocumentCodeAnalyticsResponse
)
def doccode_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_doccode_analytics(db, current_user.id)
