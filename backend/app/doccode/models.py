from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class DocumentCode(Base):
    __tablename__ = "document_codes"

    id = Column(Integer, primary_key=True, index=True)

    code = Column(String(50), unique=True, index=True, nullable=False)

    password_hash = Column(String(255), nullable=True)

    # 🔑 FILE INFO
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    mime_type = Column(String(100), nullable=False)

    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    received_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ✅ ADD THESE RELATIONSHIPS
    owner = relationship("User", foreign_keys=[owner_user_id])
    receiver = relationship("User", foreign_keys=[received_by_user_id])
