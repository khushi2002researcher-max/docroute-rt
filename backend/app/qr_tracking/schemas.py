from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from pydantic import Field
from app.qr_tracking.models import SubmissionStatus


# =====================================================
# 🔗 QR CODE RESPONSE
# =====================================================
class QRPhysicalCodeResponse(BaseModel):
    id: int
    token: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# 📄 CREATE REQUEST (FORM DATA)
# =====================================================
class QRPhysicalCreate(BaseModel):
    owner_name: str
    owner_email: EmailStr
    owner_contact: Optional[str]
    file_name: str
    restrict_public_view: bool = False


# =====================================================
# 📄 MAIN DOCUMENT RESPONSE (HISTORY TABLE)
# =====================================================
class QRPhysicalResponse(BaseModel):
    id: int
    user_id: int
    tracking_id: str
    owner_name: str
    owner_email: EmailStr
    owner_contact: Optional[str]
    file_name: str
    preview_url: str
    restrict_public_view: bool
    created_at: datetime


    qr_codes: List[QRPhysicalCodeResponse] = Field(default_factory=list)

    active_qr: Optional[QRPhysicalCodeResponse] = None

    class Config:
        from_attributes = True


# =====================================================
# 👁 SCAN LOG RESPONSE
# =====================================================
class QRScanLogResponse(BaseModel):
    id: int
    scanned_by: str
    ip_address: Optional[str]
    user_agent: Optional[str]

    country: Optional[str]
    region: Optional[str]
    city: Optional[str]

    scanned_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# 🧾 AUDIT LOG RESPONSE
# =====================================================
class QRAuditLogResponse(BaseModel):
    id: int
    action: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# 🌐 PUBLIC QR SCAN RESPONSE (USED BY /qr/scan/{token})
# =====================================================
class QRPublicViewResponse(BaseModel):
    verified: bool
    message: Optional[str] = None

    owner_name: Optional[str] = None
    owner_email: Optional[EmailStr] = None
    owner_contact: Optional[str] = None

    class Config:
        from_attributes = True


# =====================================================
# 📱 QR DETAILS PAGE RESPONSE (USED BY /qr/:token PAGE)
# =====================================================
class QRDetailsResponse(BaseModel):
    verified: bool
    message: Optional[str] = None

    tracking_id: Optional[str] = None
    file_name: Optional[str] = None

    owner_name: Optional[str] = None
    owner_email: Optional[EmailStr] = None
    owner_contact: Optional[str] = None

    class Config:
        from_attributes = True

# =====================================================
# 📱 QR LANDING PAGE RESPONSE (BEFORE LOGIN)
# =====================================================
# =====================================================
# 📱 QR LANDING PAGE RESPONSE (BEFORE LOGIN)
# =====================================================
class QRLandingResponse(BaseModel):
    restricted: bool
    message: str
    allow_owner_login: bool = True

    class Config:
        from_attributes = True






class QROwnerLoginRequest(BaseModel):
    password: str


class QROwnerLoginResponse(BaseModel):
    verified: bool
    message: Optional[str] = None

    id: int | None = None
    tracking_id: str | None = None
    file_name: str | None = None
    restrict_public_view: bool | None = None


class QRSubmissionCreate(BaseModel):
    qr_document_id: int
    submitted_to: str
    submitted_location: str
    remarks: Optional[str]



class QRSubmissionResponse(BaseModel):
    id: int
    qr_document_id: int
    file_name: str

    submitted_to: str
    submitted_location: str
    remarks: Optional[str]

    submitted_at: datetime
    received_at: Optional[datetime]
    status: SubmissionStatus

    class Config:
        from_attributes = True