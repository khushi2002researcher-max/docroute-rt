from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    UploadFile,
    File,
    Form,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql import func
from uuid import uuid4
import os
import requests
from passlib.context import CryptContext
from app.auth.utils import verify_password

from app.auth.models import User
from app.auth.utils import get_current_user
from fastapi import Query


from app.database import get_db
from app.qr_tracking.models import (
    QRPhysicalDocument,
    QRPhysicalCode,
    QRPhysicalScanLog,
    QRPhysicalAuditLog,
    QRPhysicalSubmission,
    SubmissionStatus,
)
from app.qr_tracking.schemas import (
    QRPhysicalResponse,
    QRScanLogResponse,
    QRAuditLogResponse,
    QRPublicViewResponse,
    QROwnerLoginRequest,
    QROwnerLoginResponse,
    QRSubmissionCreate,
    QRSubmissionResponse,


)

router = APIRouter(prefix="/qr", tags=["QR Physical Tracking"])

UPLOAD_DIR = "/tmp/qr_docs"

os.makedirs(UPLOAD_DIR, exist_ok=True)


# =====================================================
# 🌍 IP LOCATION LOOKUP
# =====================================================
def get_location_from_ip(ip: str):
    # Skip localhost / private IPs
    if ip in ("127.0.0.1", "localhost") or ip.startswith("192.168.") or ip.startswith("10."):
        return {
            "country": "Local",
            "region": "Local",
            "city": "Local",
        }

    try:
        res = requests.get(f"https://ipapi.co/{ip}/json/", timeout=3)
        if res.status_code != 200:
            return {}

        data = res.json()
        return {
            "country": data.get("country_name"),
            "region": data.get("region"),
            "city": data.get("city"),
        }
    except Exception:
        return {}


# =====================================================
# 📄 CREATE DOCUMENT + QR
# =====================================================
@router.post("/create", response_model=QRPhysicalResponse)
def create_qr_document(
    owner_name: str = Form(...),
    owner_email: str = Form(...),
    owner_contact: str = Form(None),
    owner_password: str = Form(...),
    file_name: str = Form(...),
    restrict_public_view: bool = Form(False),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.auth.utils import hash_password

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="PDF only allowed")

    password_hash = hash_password(owner_password)


    pdf_filename = f"{uuid4().hex}.pdf"
    pdf_path = os.path.join(UPLOAD_DIR, pdf_filename)

    with open(pdf_path, "wb") as f:
        f.write(file.file.read())

    document = QRPhysicalDocument(
    owner_name=owner_name,
    owner_email=owner_email,
    owner_contact=owner_contact,
    file_name=file_name,
    pdf_path=pdf_path,
    restrict_public_view=restrict_public_view,
    owner_password_hash=password_hash,
        user_id=user.id,

)

    db.add(document)
    db.commit()
    db.refresh(document)

    qr = QRPhysicalCode(
        document_id=document.id,
        token=uuid4().hex,
        is_active=True,
    )

    db.add(qr)
    db.add(QRPhysicalAuditLog(document_id=document.id, action="CREATE_TRACKING"))
    db.commit()

    return document


# =====================================================
# 📜 LIST DOCUMENTS
# =====================================================
@router.get("/documents", response_model=list[QRPhysicalResponse])
def list_documents(db: Session = Depends(get_db), user: User = Depends(get_current_user),):
    return (
        db.query(QRPhysicalDocument)
        .filter(QRPhysicalDocument.user_id == user.id) 
        .options(
            selectinload(QRPhysicalDocument.qr_codes),
            selectinload(QRPhysicalDocument.active_qr),
        )
        .order_by(QRPhysicalDocument.created_at.desc())
        .all()
    )


# =====================================================
# 📄 PDF PREVIEW
# =====================================================

@router.get("/preview/{doc_id}")
def preview_pdf(
    doc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    document = (
        db.query(QRPhysicalDocument)
        .filter(
            QRPhysicalDocument.id == doc_id,
            QRPhysicalDocument.user_id == user.id,
        )
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not os.path.exists(document.pdf_path):
        raise HTTPException(status_code=404, detail="File missing")

    return FileResponse(
        path=document.pdf_path,
        media_type="application/pdf",
        filename=document.file_name,
        headers={"Content-Disposition": "inline"},
    )

# =====================================================
# 🌐 PUBLIC QR SCAN
# =====================================================
@router.get("/scan/{token}", response_model=QRPublicViewResponse)
def scan_qr(token: str, request: Request, db: Session = Depends(get_db)):
    qr = (
        db.query(QRPhysicalCode)
        .filter(
            QRPhysicalCode.token == token,
            QRPhysicalCode.is_active.is_(True),
            QRPhysicalCode.revoked_at.is_(None),
        )
        .first()
    )

    if not qr:
        raise HTTPException(status_code=410, detail="QR invalid or revoked")

    document = qr.document

    ip = (
    request.headers.get("x-forwarded-for", "").split(",")[0]
    or request.client.host
)

    location = get_location_from_ip(ip) if ip else {}

    # ✅ LOG PUBLIC SCAN
    db.add(QRPhysicalScanLog(
        document_id=document.id,
        scanned_by="public",
        ip_address=ip,
        user_agent=request.headers.get("user-agent"),
        country=location.get("country"),
        region=location.get("region"),
        city=location.get("city"),
    ))

    db.add(QRPhysicalAuditLog(
        document_id=document.id,
        action="QR_PUBLIC_SCAN",
    ))

    db.commit()

    # 🔒 STRICT MODE
    if document.restrict_public_view:
        return {
            "verified": False,
            "message": "This document is restricted. Owner access required.",
        }

    # 🌍 PUBLIC MODE
    return {
        "verified": True,
        "message": "Owner details available",
        "owner_name": document.owner_name,
        "owner_email": document.owner_email,
        "owner_contact": document.owner_contact,
    }

# =====================================================
# 👁 SCAN HISTORY
# =====================================================
@router.get("/history/{doc_id}", response_model=list[QRScanLogResponse])
def scan_history(
    doc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),  # ✅ ADD
):
    document = db.query(QRPhysicalDocument).filter(
        QRPhysicalDocument.id == doc_id,
        QRPhysicalDocument.user_id == user.id,  # ✅ OWNER CHECK
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return (
        db.query(QRPhysicalScanLog)
        .filter(QRPhysicalScanLog.document_id == doc_id)
        .order_by(QRPhysicalScanLog.scanned_at.desc())
        .all()
    )


# =====================================================
# 🧾 AUDIT LOGS
# =====================================================
@router.get("/audit/{doc_id}", response_model=list[QRAuditLogResponse])
def audit_logs(
    doc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    document = db.query(QRPhysicalDocument).filter(
        QRPhysicalDocument.id == doc_id,
        QRPhysicalDocument.user_id == user.id,
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return (
        db.query(QRPhysicalAuditLog)
        .filter(QRPhysicalAuditLog.document_id == doc_id)
        .order_by(QRPhysicalAuditLog.created_at.desc())
        .all()
    )


# =====================================================
# 🔒 REVOKE QR
# =====================================================
@router.post("/revoke/{token}")
def revoke_qr(
    token: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    qr = db.query(QRPhysicalCode).filter(
        QRPhysicalCode.token == token,
        QRPhysicalCode.is_active.is_(True),
    ).first()

    if not qr or qr.document.user_id != user.id:
        raise HTTPException(status_code=404, detail="QR not found")

    qr.is_active = False
    qr.revoked_at = func.now()

    db.add(
        QRPhysicalAuditLog(
            document_id=qr.document_id,
            action="REVOKE_QR",
        )
    )

    db.commit()
    return {"status": "QR revoked"}


# =====================================================
# 🗑 DELETE DOCUMENT
# =====================================================
@router.delete("/delete/{doc_id}")
def delete_tracking(doc_id: int, db: Session = Depends(get_db),user: User = Depends(get_current_user)
):
    document = (
    db.query(QRPhysicalDocument)
    .filter(
        QRPhysicalDocument.id == doc_id,
        QRPhysicalDocument.user_id == user.id,  # ✅
    )
    .first()
)


    if not document:
        raise HTTPException(status_code=404, detail="Tracking not found")

    if document.pdf_path and os.path.exists(document.pdf_path):
        os.remove(document.pdf_path)

    db.delete(document)
    db.commit()
    return {"status": "Tracking deleted"}


# =====================================================
# 🔁 GENERATE NEW QR
# =====================================================
@router.post("/generate/{doc_id}")
def generate_new_qr(doc_id: int, db: Session = Depends(get_db),user: User = Depends(get_current_user),):
    document = (
    db.query(QRPhysicalDocument)
    .filter(
        QRPhysicalDocument.id == doc_id,
        QRPhysicalDocument.user_id == user.id,
    )
    .first()
)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # 🔥 Revoke ALL previous active QRs (IMPORTANT)
    db.query(QRPhysicalCode).filter(
        QRPhysicalCode.document_id == doc_id,
        QRPhysicalCode.is_active == True,
    ).update(
        {
            QRPhysicalCode.is_active: False,
            QRPhysicalCode.revoked_at: func.now(),
        },
        synchronize_session=False,
    )

    # ✅ Create new active QR
    new_qr = QRPhysicalCode(
        document_id=doc_id,
        token=uuid4().hex,
        is_active=True,
    )

    db.add(new_qr)
    db.add(
        QRPhysicalAuditLog(
            document_id=doc_id,
            action="GENERATE_NEW_QR",
        )
    )

    db.commit()
    return {"token": new_qr.token}




@router.post("/owner-login/{token}")
def owner_login(
    token: str,
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
):
    qr = (
    db.query(QRPhysicalCode)
    .filter(
        QRPhysicalCode.token == token,
        QRPhysicalCode.is_active.is_(True),
        QRPhysicalCode.revoked_at.is_(None),
    )
    .first()
)


    if not qr:
        raise HTTPException(status_code=404, detail="Invalid QR")

    document = qr.document
    password = payload.get("password")

    if not password:
        raise HTTPException(status_code=400, detail="Password required")

    if not verify_password(password, document.owner_password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")

    # ✅ FIXED: IP + LOCATION (INSIDE FUNCTION)
    ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0]
        or request.client.host
    )

    location = get_location_from_ip(ip) if ip else {}

    # ✅ LOG OWNER SCAN
    db.add(QRPhysicalScanLog(
        document_id=document.id,
        scanned_by="owner",
        ip_address=ip,
        user_agent=request.headers.get("user-agent"),
        country=location.get("country"),
        region=location.get("region"),
        city=location.get("city"),
    ))

    # ✅ AUDIT LOG
    db.add(QRPhysicalAuditLog(
        document_id=document.id,
        action="OWNER_LOGIN",
        ip_address=ip,
        user_agent=request.headers.get("user-agent"),
    ))

    db.commit()

    return {
        "id": document.id,
        "tracking_id": document.tracking_id,
        "file_name": document.file_name,
        "pdf_preview": f"/qr/preview/{document.id}",
    }




@router.post("/submission", response_model=QRSubmissionResponse)
def create_submission(
    payload: QRSubmissionCreate,
    db: Session = Depends(get_db),
):
    document = (
        db.query(QRPhysicalDocument)
        .filter(QRPhysicalDocument.id == payload.qr_document_id)
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    submission = QRPhysicalSubmission(
        qr_document_id=document.id,
        file_name=document.file_name,   # ✅ AUTO
        submitted_to=payload.submitted_to,
        submitted_location=payload.submitted_location,
        remarks=payload.remarks,
        status=SubmissionStatus.SUBMITTED,
    )

    db.add(submission)
    db.add(QRPhysicalAuditLog(
        document_id=document.id,
        action="SUBMISSION_CREATED",
    ))
    db.commit()
    db.refresh(submission)

    return submission


@router.get("/submission/{doc_id}", response_model=list[QRSubmissionResponse])
def list_submissions(doc_id: int, db: Session = Depends(get_db)):
    return (
        db.query(QRPhysicalSubmission)
        .filter(QRPhysicalSubmission.qr_document_id == doc_id)
        .order_by(QRPhysicalSubmission.submitted_at.desc())
        .all()
    )


@router.post("/submission/{submission_id}/receive")
def receive_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    submission = (
        db.query(QRPhysicalSubmission)
        .filter(QRPhysicalSubmission.id == submission_id)
        .first()
    )

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    document = submission.document

    if document.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    submission.status = SubmissionStatus.RECEIVED
    submission.received_at = func.now()

    db.add(QRPhysicalAuditLog(
        document_id=submission.qr_document_id,
        action="SUBMISSION_RECEIVED",
    ))

    db.commit()

    return {"status": "RECEIVED"}



@router.delete("/submission/{submission_id}")
def delete_submission(
    submission_id: int,
    db: Session = Depends(get_db),
):
    submission = (
        db.query(QRPhysicalSubmission)
        .filter(QRPhysicalSubmission.id == submission_id)
        .first()
    )

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    db.delete(submission)
    db.commit()

    return {"status": "submission deleted"}


@router.delete("/audit/{audit_id}")
def delete_audit(
    audit_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    audit = db.query(QRPhysicalAuditLog).filter(
        QRPhysicalAuditLog.id == audit_id
    ).first()

    if not audit or audit.document.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    db.delete(audit)
    db.commit()

    return {"status": "audit deleted"}



@router.delete("/history/{scan_id}")
def delete_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    scan = db.query(QRPhysicalScanLog).filter(
        QRPhysicalScanLog.id == scan_id
    ).first()

    if not scan or scan.document.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    db.delete(scan)
    db.commit()

    return {"status": "scan deleted"}
