import secrets
import string
import re
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.doccode.models import DocumentCode

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =====================================================
# 🔐 CODE GENERATION
# =====================================================
def generate_secure_code(length: int = 16) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


# =====================================================
# 🔑 PASSWORD VALIDATION
# =====================================================
def validate_password(password: str):
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password too long (max 72 bytes)")

    if len(password) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password must be at least 8 characters")

    if not re.search(r"[A-Z]", password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password must contain an uppercase letter")

    if not re.search(r"[a-z]", password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password must contain a lowercase letter")

    if not re.search(r"\d", password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password must contain a number")

    if not re.search(r"[!@#$%^&*()_+=\-{}\[\]:\";'<>?,./]", password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password must contain a special character")


# =====================================================
# 🔐 HASH / VERIFY
# =====================================================
def hash_password(password: str) -> str:
    safe = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    return pwd_context.hash(safe)


def verify_password(password: str, hashed: str) -> bool:
    safe = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    return pwd_context.verify(safe, hashed)


# =====================================================
# 📤 CREATE DOCUMENT CODE
# =====================================================
def create_document_code(
    db: Session,
    user_id: int,
    file_name: str,
    file_path: str,
    file_type: str,
    mime_type: str,
    password: str | None,
):
    if password:
        validate_password(password)

    # 🔁 Ensure unique code
    while True:
        code = generate_secure_code()
        if not db.query(DocumentCode).filter_by(code=code).first():
            break

    record = DocumentCode(
        code=code,
        file_name=file_name,
        file_path=file_path,
        file_type=file_type,
        mime_type=mime_type,
        owner_user_id=user_id,
        password_hash=hash_password(password) if password else None,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        is_used=False,
    )

    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to create document code"
        )

    return record


# =====================================================
# 📥 RECEIVE DOCUMENT CODE
# =====================================================
def receive_document_code(
    db: Session,
    code: str,
    password: str | None,
    receiver_user_id: int,
):
    code = code.strip().upper()  # 🔥 normalize input

    record = db.query(DocumentCode).filter_by(code=code).first()

    if not record:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invalid code")

    if record.is_used:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Code already used")

    if record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_410_GONE, "Code expired")

    if record.password_hash:
        if not password:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password required")

        if not verify_password(password, record.password_hash):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid password")

    if record.owner_user_id == receiver_user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot receive your own document")

    try:
        record.is_used = True
        record.received_by_user_id = receiver_user_id
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to receive document"
        )

    return record


# =====================================================
# 📜 HISTORY
# =====================================================
def get_sender_history(db: Session, user_id: int):
    return (
        db.query(DocumentCode)
        .filter(DocumentCode.owner_user_id == user_id)
        .order_by(DocumentCode.created_at.desc())
        .all()
    )


def get_receiver_history(db: Session, user_id: int):
    return (
        db.query(DocumentCode)
        .filter(DocumentCode.received_by_user_id == user_id)
        .order_by(DocumentCode.created_at.desc())
        .all()
    )
