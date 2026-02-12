from fastapi import Depends, Header, HTTPException, status, Request
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from uuid import uuid4
from typing import Dict, Optional
from datetime import datetime, timedelta
import difflib
import json
import os

from app.database import get_db

# ✅ MODELS
from app.auth.models import User
from app.document.D_models import (
    Document,
    DocumentAccess,
    DocumentShareLink,
)

SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_THIS_IN_PRODUCTION")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# =========================
# PASSWORD UTILS
# =========================

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


# =========================
# SIMPLE TOKEN STORE (DEV)
# =========================

tokens: Dict[str, int] = {}

def create_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "exp": expire,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def revoke_token(token: str):
    pass  # JWT handled via expiration

# =========================
# AUTH DEPENDENCY
# =========================

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format",
        )

    token = authorization.split(" ", 1)[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
    )


    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


# =========================
# DOCUMENT PERMISSION CHECK
# =========================

def check_document_permission(
    *,
    user: User,
    document: Document,
    required_permission: str,  # view | edit
    db: Session,
):
    # Owner has full access
    if document.owner_id == user.id:
        return

    access = (
        db.query(DocumentAccess)
        .filter(
            DocumentAccess.document_id == document.id,
            DocumentAccess.user_id == user.id,
            DocumentAccess.revoked_at.is_(None),
        )
        .first()
    )

    if not access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this document",
        )

    if required_permission == "edit" and access.permission != "edit":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Edit permission required",
        )


# =========================
# TRACKING ID
# =========================

def generate_tracking_id() -> str:
    return f"DOC-{uuid4().hex[:12].upper()}"


# =========================
# VERSION DIFF
# =========================

def generate_diff(
    old_text: Optional[str],
    new_text: Optional[str],
) -> str:
    old_lines = (old_text or "").splitlines()
    new_lines = (new_text or "").splitlines()

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile="previous",
        tofile="current",
        lineterm="",
    )

    return "\n".join(diff)


# =========================
# LIVE VIEWERS (IN-MEMORY)
# =========================

_live_viewers: Dict[int, Dict[int, datetime]] = {}


def register_live_view(document_id: int, user_id: int):
    now = datetime.utcnow()
    viewers = _live_viewers.setdefault(document_id, {})
    viewers[user_id] = now


def cleanup_live_viewers(timeout_seconds: int = 60):
    now = datetime.utcnow()

    for doc_id in list(_live_viewers.keys()):
        viewers = _live_viewers[doc_id]

        for uid in list(viewers.keys()):
            if (now - viewers[uid]).total_seconds() > timeout_seconds:
                viewers.pop(uid)

        if not viewers:
            _live_viewers.pop(doc_id)


def get_live_viewers(document_id: int) -> Dict[int, datetime]:
    cleanup_live_viewers()
    return _live_viewers.get(document_id, {})


# =========================
# SHARE LINK VALIDATION
# =========================

def is_share_link_valid(link: DocumentShareLink) -> bool:
    if not link.is_active:
        return False

    if link.expires_at and datetime.utcnow() > link.expires_at:
        return False

    return True


def verify_share_link_password(
    link: DocumentShareLink,
    password: Optional[str],
):
    if link.password_hash:
        if not password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password required for this share link",
            )
        if not verify_password(password, link.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid share link password",
            )


def check_share_permission(
    link: DocumentShareLink,
    required_permission: str,  # view | download | edit
):
    hierarchy = {"view": 1, "download": 2, "edit": 3}

    if hierarchy.get(link.permission, 0) < hierarchy.get(required_permission, 0):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Share link does not allow this action",
        )


# =========================
# 🔥 SHARE MODE CHECK (LINK / QR)
# =========================

def check_share_mode(
    link: DocumentShareLink,
    via: str,  # link | qr
):
    if link.share_mode != via:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This document must be accessed via {link.share_mode.upper()}",
        )


# =========================
# SHARE EXPIRY
# =========================

def build_share_expiry(hours: Optional[int] = None) -> Optional[datetime]:
    if not hours:
        return None
    return datetime.utcnow() + timedelta(hours=hours)


# =========================
# 🔥 REVOKE SHARE LINK
# =========================

def revoke_share_link(link: DocumentShareLink):
    link.is_active = False
    link.revoked_at = datetime.utcnow()



# =========================
# 📊 CLIENT / AUDIT METADATA
# =========================

def build_client_info(request: Optional[Request]) -> Optional[str]:
    if not request:
        return None

    info = {
        "ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }

    return json.dumps(info)


# =====================================================
# 🔳 QR DOCUMENT UTILITIES (NEW MODULE)
# =====================================================

# -----------------------------------------------------
# QR TRACKING ID (FOR PHYSICAL / PRINTED DOCS)
# -----------------------------------------------------

def generate_qr_tracking_id() -> str:
    """
    Generates human-readable tracking ID for QR documents
    Example: QR-9F2A81C3
    """
    return f"QR-{uuid4().hex[:8].upper()}"


# -----------------------------------------------------
# QR TOKEN (PUBLIC SAFE IDENTIFIER)
# -----------------------------------------------------

def generate_qr_token() -> str:
    """
    Secure, non-guessable token embedded in QR code
    """
    return uuid4().hex


# -----------------------------------------------------
# QR ROLE DETECTION
# -----------------------------------------------------

def detect_scan_role(
    *,
    current_user: Optional[User],
    owner_id: int,
) -> str:
    """
    Determines if scan is by OWNER or PUBLIC
    """
    if current_user and current_user.id == owner_id:
        return "owner"
    return "public"


# -----------------------------------------------------
# GEOLOCATION PARSER (IP / BROWSER DATA)
# -----------------------------------------------------

def build_qr_scan_metadata(
    request: Optional[Request],
    geo_data: Optional[dict] = None,
) -> dict:
    """
    Collects scan metadata safely
    """
    meta = {}

    if request:
        meta["ip_address"] = request.client.host if request.client else None
        meta["user_agent"] = request.headers.get("user-agent")

    if geo_data:
        meta.update({
            "country": geo_data.get("country"),
            "city": geo_data.get("city"),
            "latitude": geo_data.get("latitude"),
            "longitude": geo_data.get("longitude"),
        })

    return meta


# -----------------------------------------------------
# 🔴 RED-FLAG DOCUMENT RULE
# -----------------------------------------------------

def is_public_view_allowed(
    *,
    is_red_flag: bool,
) -> bool:
    """
    Red-flag documents restrict public details
    """
    return not is_red_flag


# -----------------------------------------------------
# 🔐 QR ACCESS VALIDATION
# -----------------------------------------------------

def validate_qr_access(
    *,
    is_active: bool,
    revoked_at: Optional[datetime],
):
    if not is_active or revoked_at:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="QR code has been revoked",
        )
