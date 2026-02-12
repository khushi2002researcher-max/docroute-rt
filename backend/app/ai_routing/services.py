import re
from datetime import date, datetime
from typing import List, Optional, Dict, TypedDict

from app.email import send_reminder_email

from app.ai_routing.models import (
    AIDecisionFlag,
    PriorityLevel,
    DeadlineLabel,
    RoutingSource,
)
from app.ai_routing.models import DocumentCategory



# =====================================================
# CONFIGURATION
# =====================================================

CONFIDENCE_THRESHOLD: float = 0.85
DEADLINE_NEAR_DAYS = 5
DEADLINE_CRITICAL_DAYS = 1


# =====================================================
# TYPES
# =====================================================

class DetectedDeadline(TypedDict):
    deadline_date: date
    label: DeadlineLabel
    confidence: float


# =====================================================
# DATE UTILITIES
# =====================================================

def calculate_days_remaining(deadline: date) -> int:
    return (deadline - date.today()).days


# =====================================================
# AI FLAG ENGINE
# =====================================================

def calculate_ai_flag(deadline: Optional[date]) -> AIDecisionFlag:
    if not deadline:
        return AIDecisionFlag.DATE_MISSING

    days = calculate_days_remaining(deadline)

    if days < 0:
        return AIDecisionFlag.MISSED_DEADLINE
    if days <= DEADLINE_CRITICAL_DAYS:
        return AIDecisionFlag.DEADLINE_CRITICAL
    if days <= DEADLINE_NEAR_DAYS:
        return AIDecisionFlag.DEADLINE_NEAR

    return AIDecisionFlag.DEADLINE_FOUND


# =====================================================
# PRIORITY ENGINE
# =====================================================

def calculate_priority(deadline: Optional[date]) -> PriorityLevel:
    if not deadline:
        return PriorityLevel.MEDIUM

    days = calculate_days_remaining(deadline)

    if days <= DEADLINE_CRITICAL_DAYS:
        return PriorityLevel.CRITICAL
    if days <= DEADLINE_NEAR_DAYS:
        return PriorityLevel.HIGH

    return PriorityLevel.MEDIUM


# =====================================================
# HUMAN REVIEW DECISION
# =====================================================

def requires_human_review(
    deadline: Optional[date],
    confidence: Optional[float],
) -> bool:
    if not deadline or confidence is None:
        return True
    return confidence < CONFIDENCE_THRESHOLD


# =====================================================
# AI DEADLINE EXTRACTION
# =====================================================

def extract_deadlines_from_text(text: str) -> List[DetectedDeadline]:
    results: List[DetectedDeadline] = []

    if not text:
        return results

    text_lower = text.lower()

    patterns = [
        (r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", ["%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"]),
        (r"\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b", ["%d %b %Y", "%d %B %Y"]),
        (r"\b([A-Za-z]{3,9}\s+\d{1,2},\s*\d{4})\b", ["%b %d, %Y", "%B %d, %Y"]),
    ]

    for pattern, formats in patterns:
        for match in re.findall(pattern, text):
            for fmt in formats:
                try:
                    parsed = datetime.strptime(
                        match.replace("-", "/"), fmt
                    ).date()

                    # ✅ SMART LABEL DETECTION
                    label = DeadlineLabel.DUE

                    if "submit" in text_lower or "submission" in text_lower:
                        label = DeadlineLabel.SUBMISSION
                    elif "expire" in text_lower or "expiry" in text_lower:
                        label = DeadlineLabel.EXPIRY
                    elif "renew" in text_lower:
                        label = DeadlineLabel.RENEWAL
                    elif "hearing" in text_lower:
                        label = DeadlineLabel.HEARING

                    results.append({
                        "deadline_date": parsed,
                        "label": label,
                        "confidence": 0.9 if "%Y" in fmt else 0.7,
                    })
                    break

                except ValueError:
                    continue

    return results


# =====================================================
# 📄 DOCUMENT TYPE CLASSIFICATION
# =====================================================

def classify_document(text: str) -> DocumentCategory:
    if not text:
        return DocumentCategory.OTHER

    text_lower = text.lower()

    # AGREEMENT / CONTRACT
    if any(k in text_lower for k in [
        "agreement",
        "contract",
        "hereby agree",
        "terms and conditions",
        "party of the first part",
        "party of the second part",
    ]):
        return DocumentCategory.AGREEMENT

    # LEGAL
    if any(k in text_lower for k in [
        "court",
        "legal",
        "plaintiff",
        "defendant",
        "section",
        "act",
        "law",
        "jurisdiction",
    ]):
        return DocumentCategory.LEGAL

    # SUBMISSION
    if any(k in text_lower for k in [
        "submit",
        "submission",
        "apply",
        "application",
        "filing",
        "filed on",
    ]):
        return DocumentCategory.SUBMISSION

    # INVOICE
    if any(k in text_lower for k in [
        "invoice",
        "amount due",
        "total payable",
        "gst",
        "tax",
        "bill number",
    ]):
        return DocumentCategory.INVOICE

    # POLICY
    if any(k in text_lower for k in [
        "policy",
        "guidelines",
        "compliance",
        "procedure",
        "framework",
    ]):
        return DocumentCategory.POLICY

    # NOTICE
    if any(k in text_lower for k in [
        "notice",
        "hereby informed",
        "intimation",
        "this is to notify",
    ]):
        return DocumentCategory.NOTICE

    return DocumentCategory.OTHER


# =====================================================
# AMBIGUITY DETECTION
# =====================================================

def detect_ambiguity(deadlines: List[DetectedDeadline]) -> bool:
    return len({d["deadline_date"] for d in deadlines}) > 1


# =====================================================
# EMAIL COMPOSITION
# =====================================================

def build_deadline_email(
    *,
    document_name: str,
    routing_id: str,
    deadline: date,
    days_remaining: int,
    priority: PriorityLevel,
    flag: AIDecisionFlag,
    source: RoutingSource,
) -> tuple[str, str]:
    subject = f"⏰ Deadline Reminder – {routing_id}"

    body = f"""
Document: {document_name}
Routing ID: {routing_id}

Deadline: {deadline}
Days Remaining: {days_remaining}

Priority: {priority.value}
Status: {flag.value}
Source: {source.value}

Immediate action recommended.
"""

    return subject.strip(), body.strip()


# =====================================================
# EMAIL SENDER
# =====================================================
def send_deadline_notification(
    *,
    primary_email: str,
    document_name: str,
    routing_id: str,
    deadline: date,
    priority: PriorityLevel,
    flag: AIDecisionFlag,
    source: RoutingSource,
    extra_emails: Optional[List[str]] = None,
):
    days_remaining = calculate_days_remaining(deadline)

    subject, body = build_deadline_email(
        document_name=document_name,
        routing_id=routing_id,
        deadline=deadline,
        days_remaining=days_remaining,
        priority=priority,
        flag=flag,
        source=source,
    )

    send_reminder_email(
        to=primary_email,
        subject=subject,
        text_body=body,
    )

    if extra_emails:
        for email in extra_emails:
            send_reminder_email(
                to=email,
                subject=subject,
                text_body=body,
            )

# =====================================================
# REMINDER TRIGGER
# =====================================================

def should_trigger_notification(
    *,
    deadline: date,
    flag: AIDecisionFlag,
) -> bool:
    days = calculate_days_remaining(deadline)
    return days in {DEADLINE_NEAR_DAYS, 1, 0} or days < 0


# =====================================================
# ESCALATION ENGINE
# =====================================================

def should_escalate(
    *,
    deadline: date,
    priority: PriorityLevel,
) -> bool:
    days = calculate_days_remaining(deadline)
    return days < 0 or priority == PriorityLevel.CRITICAL
