from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional
from pydantic import field_validator


# =======================
# USER SCHEMAS
# =======================

class RegisterSchema(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


# =======================
# OCR SCHEMAS
# =======================

class OCRCreate(BaseModel):
    filename: str
    extracted_text: str


class OCRResponse(BaseModel):
    id: int
    filename: str
    extracted_text: str
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# =======================
# AI DOCUMENT SCHEMAS
# =======================

class AIDocumentCreate(BaseModel):
    file_name: str
    input_text: str

    language: str = "english"      # english | hindi
    length: str = "short"
    format: str = "paragraph"

    summary: Optional[str] = None
    tags: Optional[List[str]] = None

    @field_validator("language")
    @classmethod
    def validate_language(cls, v):
        if v not in ["english", "hindi"]:
            raise ValueError("Only english and hindi are supported")
        return v

class AIResponse(BaseModel):
    id: int
    file_name: str
    input_text: str

    # 🔥 SAVE USER OPTIONS
    language: str
    length: str
    format: str

    # 🔁 AI OUTPUT
    summary: Optional[str]
    tags: Optional[List[str]]

    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# =======================
# DOCUMENT SCHEMAS
# =======================

class DocumentBase(BaseModel):
    file_name: str
    file_type: str
    content: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    file_name: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None


class DocumentOwner(BaseModel):
    id: int
    full_name: str
    email: EmailStr

    class Config:
        from_attributes = True


class DocumentResponse(DocumentBase):
    id: int
    tracking_id: str
    owner: DocumentOwner

    created_at: datetime
    last_updated_at: datetime

    last_viewed_at: Optional[datetime]
    last_viewed_by: Optional[int]

    is_deleted: bool

    class Config:
        from_attributes = True


# =======================
# DOCUMENT VERSION
# =======================

class DocumentVersionResponse(BaseModel):
    id: int
    version_number: int
    content: Optional[str]
    diff: Optional[str]

    created_at: datetime
    created_by: int

    class Config:
        from_attributes = True


class DocumentVersionWithUserResponse(DocumentVersionResponse):
    created_by_user: Optional[DocumentOwner]


class DocumentRestoreResponse(BaseModel):
    document_id: int
    restored_version_id: int
    restored_at: datetime


# =======================
# DOCUMENT ACCESS
# =======================

class DocumentAccessCreate(BaseModel):
    user_id: int
    permission: str  # view | edit


class DocumentAccessResponse(BaseModel):
    id: int
    document_id: int
    user_id: int
    permission: str
    granted_by: int
    granted_at: datetime
    revoked_at: Optional[datetime]

    class Config:
        from_attributes = True


class DocumentAccessUserResponse(BaseModel):
    user: DocumentOwner
    permission: str

    class Config:
        from_attributes = True


# =======================
# AUDIT LOG
# =======================

class AuditLogResponse(BaseModel):
    id: int
    module: str
    action: str
    event_type: Optional[str]

    document_id: int
    performed_by_user: Optional[DocumentOwner]

    extra_data: Optional[str]
    client_info: Optional[str]

    created_at: datetime

    class Config:
        from_attributes = True


# =======================
# LIVE VIEWERS
# =======================

class LiveViewerResponse(BaseModel):
    user: Optional[DocumentOwner]
    last_ping_at: datetime

    class Config:
        from_attributes = True


class DocumentLiveViewersResponse(BaseModel):
    document_id: int
    viewers: List[LiveViewerResponse]


# =======================
# SHARE LINKS (LINK + QR)
# =======================

class DocumentShareLinkCreate(BaseModel):
    share_mode: str = "link"          # link | qr
    permission: str = "view"          # view | edit | download
    expires_at: Optional[datetime] = None
    password: Optional[str] = None


class DocumentShareLinkResponse(BaseModel):
    id: int
    document_id: int
    token: str

    share_mode: str
    permission: str
    password_required: bool

    is_active: bool
    revoked_at: Optional[datetime]

    opened_count: int
    last_opened_at: Optional[datetime]

    created_by: int
    creator: Optional[DocumentOwner]

    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# =======================
# DOWNLOAD TRACKING
# =======================

class DocumentDownloadLogResponse(BaseModel):
    id: int
    document_id: int
    downloaded_by: Optional[int]
    format: str
    downloaded_at: datetime
    client_info: Optional[str]

    class Config:
        from_attributes = True


# =======================
# SHARED DOCUMENT RESPONSE
# =======================

class SharedDocumentResponse(BaseModel):
    document_id: int
    content: str

    watermark: str
    permission: str        # view | edit | download
    share_mode: str        # link | qr
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True




class ForgotPasswordSchema(BaseModel):
    email: EmailStr

class ResetPasswordSchema(BaseModel):
    new_password: str