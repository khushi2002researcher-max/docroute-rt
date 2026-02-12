from pydantic import BaseModel, field_validator
from datetime import datetime, timezone
from typing import Optional


# =====================================================
# 📤 GENERATE CODE RESPONSE
# =====================================================
class GenerateCodeResponse(BaseModel):
    code: str
    file_name: str
    expires_at: datetime

    model_config = {
        "from_attributes": True
    }

    @field_validator("expires_at")
    @classmethod
    def ensure_timezone(cls, v):
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


# =====================================================
# 📥 RECEIVE CODE REQUEST
# =====================================================
class ReceiveCodeRequest(BaseModel):
    code: str
    password: Optional[str] = None

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        if not v or len(v) < 6:
            raise ValueError("Invalid code format")
        return v.strip().upper()


# =====================================================
# 📜 DOCUMENT CODE HISTORY
# =====================================================
class DocumentCodeHistory(BaseModel):
    code: str
    file_name: str
    file_type: str

    created_at: datetime
    expires_at: datetime

    is_used: bool

    # 👤 Ownership
    owner_user_id: int
    received_by_user_id: Optional[int]

    # ⭐ Optional: Helpful for frontend
    status: Optional[str] = None  # active | expired | used

    model_config = {
        "from_attributes": True
    }
