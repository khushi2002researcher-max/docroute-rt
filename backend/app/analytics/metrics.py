from typing import List, Tuple, Dict
from datetime import date


# =====================================================
# 📈 TIME SERIES
# =====================================================

def build_time_series(label: str, rows: List[Tuple[date, int]]) -> Dict:
    return {
        "label": label,
        "data": [
            {"date": row[0], "value": row[1]}
            for row in rows
        ],
    }


# =====================================================
# 📊 OVERVIEW KPIs
# =====================================================

def build_overview_kpis(
    total_documents: int,
    ocr_processed: int,
    ai_analyzed: int,
    active_deadlines: int,
    pending_reminders: int,
    missed_deadlines: int,
) -> Dict:
    return {
        "total_documents": total_documents,
        "ocr_processed": ocr_processed,
        "ai_analyzed": ai_analyzed,
        "active_deadlines": active_deadlines,
        "pending_reminders": pending_reminders,
        "missed_deadlines": missed_deadlines,
    }


# =====================================================
# 🔀 WORKFLOW ANALYTICS
# =====================================================

def build_workflow_analytics(
    routing_rows: List[Tuple[str, int]],
    deadline_rows: List[Tuple[str, int]],
) -> Dict:
    return {
        "routing": [
            {"label": label, "value": count}
            for label, count in routing_rows
        ],
        "deadlines": [
            {"priority": priority, "count": count}
            for priority, count in deadline_rows
        ],
    }


# =====================================================
# ⏰ REMINDER ANALYTICS
# =====================================================

def build_reminder_analytics(
    status_rows: List[Tuple[str, int]],
    failed_today: int,
) -> Dict:
    return {
        "data": [
            {"status": status, "count": count}
            for status, count in status_rows
        ],
        "failed_today": failed_today,
    }


# =====================================================
# 🧾 AUDIT LOGS
# =====================================================

def build_audit_logs(logs) -> Dict:
    return {
        "logs": [
            {
                "id": log.id,
                "action": log.action,
                "details": getattr(log, "details", None),
                "performed_by": str(log.performed_by),
                "created_at": log.created_at,
            }
            for log in logs
        ]
    }


# =====================================================
# 🩺 SYSTEM HEALTH
# =====================================================

def build_system_health(status_map: Dict[str, bool]) -> Dict:
    return {
        "services": [
            {
                "service": service,
                "status": "OK" if ok else "FAIL",
            }
            for service, ok in status_map.items()
        ]
    }


# =====================================================
# 📄 DOCUMENT CODE ANALYTICS (NEW)
# =====================================================

def build_doccode_analytics(
    sent_total: int,
    received_total: int,
    used_codes: int,
    pending_codes: int,
) -> Dict:
    return {
        "sent_total": sent_total,
        "received_total": received_total,
        "used_codes": used_codes,
        "pending_codes": pending_codes,
    }
