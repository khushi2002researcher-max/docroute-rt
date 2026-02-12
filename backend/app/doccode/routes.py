from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from urllib.parse import quote
from datetime import datetime, timezone
import os
from uuid import uuid4

from app.database import get_db
from app.auth.utils import get_current_user
from app.auth.models import User
from app.doccode import services
from app.doccode.schemas import (
    GenerateCodeResponse,
    ReceiveCodeRequest,
    DocumentCodeHistory,
)

router = APIRouter(prefix="/doc-code", tags=["Document Code Exchange"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "doccode")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 🔒 10MB LIMIT
MAX_FILE_SIZE = 10 * 1024 * 1024  

ALLOWED_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
}

# =====================================================
# 🔐 GENERATE DOCUMENT CODE
# =====================================================
@router.post("/generate", response_model=GenerateCodeResponse)
async def generate_code(
    file: UploadFile = File(...),
    password: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid file")

    file_ext = file.filename.split(".")[-1].lower()

    if file_ext not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    safe_filename = file.filename.replace(" ", "_")
    unique_name = f"{uuid4().hex}_{safe_filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as f:
        f.write(content)

    record = services.create_document_code(
        db=db,
        user_id=user.id,
        file_name=file.filename,
        file_path=file_path,
        file_type=file_ext,
        mime_type=ALLOWED_TYPES[file_ext],
        password=password,
    )

    return {
        "code": record.code,
        "file_name": record.file_name,
        "expires_at": record.expires_at,
    }


# =====================================================
# 📥 RECEIVE & DOWNLOAD DOCUMENT
# =====================================================
@router.post("/receive")
def receive_and_download(
    payload: ReceiveCodeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = services.receive_document_code(
        db=db,
        code=payload.code,
        password=payload.password,
        receiver_user_id=user.id,
    )

    # 🔒 Expiry Safety
    if record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Code expired")

    # 🔒 File existence check
    if not os.path.exists(record.file_path):
        raise HTTPException(status_code=404, detail="File not found")

    quoted = quote(record.file_name)

    response = FileResponse(
        path=record.file_path,
        media_type=record.mime_type,
    )

    response.headers["Content-Disposition"] = (
        f"attachment; filename*=UTF-8''{quoted}"
    )

    return response


# =====================================================
# 📤 SENDER HISTORY
# =====================================================
@router.get(
    "/history/sent",
    response_model=list[DocumentCodeHistory],
)
def sender_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return services.get_sender_history(db, user.id)


# =====================================================
# 📥 RECEIVER HISTORY
# =====================================================
@router.get(
    "/history/received",
    response_model=list[DocumentCodeHistory],
)
def receiver_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return services.get_receiver_history(db, user.id)
