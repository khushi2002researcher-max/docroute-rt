from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    TIMESTAMP,
    ForeignKey,
    Boolean,
    CheckConstraint,
    DateTime
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY


from app.database import Base


# =======================
# USER MODEL
# =======================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    avatar_url = Column(String(255), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # ✅ RESET PASSWORD FIELDS
    reset_token = Column(String, nullable=True)
    reset_token_expiry = Column(DateTime(timezone=True), nullable=True)



    # =======================
    # OCR / AI RELATIONSHIPS
    # =======================
    ocr_histories = relationship(
        "OCRHistory",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    ai_documents = relationship(
        "AIDocument",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # =======================
    # DOCUMENT SYSTEM
    # =======================
    documents = relationship(
        "Document",
        back_populates="owner",
        cascade="all, delete-orphan",
        foreign_keys="Document.owner_id",
    )

    document_access = relationship(
        "DocumentAccess",
        back_populates="user",
        foreign_keys="DocumentAccess.user_id",
        cascade="all, delete-orphan",
    )

    granted_document_access = relationship(
        "DocumentAccess",
        back_populates="granted_by_user",
        foreign_keys="DocumentAccess.granted_by",
        cascade="all, delete-orphan",
    )

    audit_logs = relationship(
        "AuditLog",
        back_populates="performed_by_user",
        foreign_keys="AuditLog.performed_by",
        cascade="all, delete-orphan",
    )

    qr_documents = relationship(
    "QRPhysicalDocument",
    back_populates="user",
    cascade="all, delete-orphan"
    )

# =======================
# AI ROUTING SYSTEM
# =======================
    routing_records = relationship(
        "DocumentRouting",
        backref="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )






# =======================
# OCR HISTORY
# =======================
class OCRHistory(Base):
    __tablename__ = "ocr_history"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    extracted_text = Column(Text, nullable=False)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="ocr_histories")


# =======================
# AI DOCUMENT
# =======================
class AIDocument(Base):
    __tablename__ = "ai_documents"

    __table_args__ = (
        CheckConstraint(
            "language IN ('english', 'hindi')",
            name="check_ai_language"
        ),
    )

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    file_name = Column(Text, nullable=False)
    input_text = Column(Text, nullable=False)

    language = Column(String(20), default="english", nullable=False)
    length = Column(String(20), default="short", nullable=False)
    format = Column(String(20), default="paragraph", nullable=False)

    summary = Column(Text, nullable=True)
    tags = Column(ARRAY(Text), nullable=True)

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="ai_documents")


