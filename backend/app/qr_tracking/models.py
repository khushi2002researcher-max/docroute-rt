from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    TIMESTAMP,
    ForeignKey,
    Index,
    CheckConstraint,
    Enum,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
import enum

from app.database import Base


# =====================================================
# TRACKING ID GENERATOR
# =====================================================
def generate_tracking_id():
    return f"QR-{uuid4().hex[:10].upper()}"


# =====================================================
# 📄 PHYSICAL DOCUMENT
# =====================================================
class QRPhysicalDocument(Base):
    __tablename__ = "qr_physical_documents"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tracking_id = Column(
        String(20),  # optimized length
        unique=True,
        nullable=False,
        index=True,
        default=generate_tracking_id,
    )

    owner_name = Column(String(100), nullable=False)
    owner_email = Column(String(150), nullable=False)
    owner_contact = Column(String(30), nullable=True)

    owner_password_hash = Column(String(255), nullable=False)

    file_name = Column(String(255), nullable=False)
    pdf_path = Column(Text, nullable=False)

    restrict_public_view = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # ================= RELATIONSHIPS =================

    user = relationship(
        "User",
        back_populates="qr_documents",
    )

    submissions = relationship(
        "QRPhysicalSubmission",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    qr_codes = relationship(
        "QRPhysicalCode",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    scan_logs = relationship(
        "QRPhysicalScanLog",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    audit_logs = relationship(
        "QRPhysicalAuditLog",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    active_qr = relationship(
        "QRPhysicalCode",
        primaryjoin=(
            "and_("
            "QRPhysicalCode.document_id == QRPhysicalDocument.id, "
            "QRPhysicalCode.is_active == True)"
        ),
        uselist=False,
        viewonly=True,
        lazy="selectin",
    )


# =====================================================
# 🔗 QR CODE
# =====================================================
class QRPhysicalCode(Base):
    __tablename__ = "qr_physical_codes"

    id = Column(Integer, primary_key=True, index=True)

    document_id = Column(
        Integer,
        ForeignKey("qr_physical_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    token = Column(String(64), unique=True, index=True, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    revoked_at = Column(TIMESTAMP(timezone=True), nullable=True)

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    document = relationship(
        "QRPhysicalDocument",
        back_populates="qr_codes",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_qr_physical_code_active", "is_active"),
    )


# =====================================================
# 👁 QR SCAN LOG
# =====================================================
class QRPhysicalScanLog(Base):
    __tablename__ = "qr_physical_scan_logs"

    id = Column(Integer, primary_key=True, index=True)

    document_id = Column(
        Integer,
        ForeignKey("qr_physical_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    scanned_by = Column(String(20), nullable=False)  # public | owner
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)

    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)

    scanned_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    document = relationship(
        "QRPhysicalDocument",
        back_populates="scan_logs",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint(
            "scanned_by IN ('public','owner')",
            name="ck_qr_scan_role",
        ),
    )


# =====================================================
# 🧾 AUDIT LOG
# =====================================================
class QRPhysicalAuditLog(Base):
    __tablename__ = "qr_physical_audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    document_id = Column(
        Integer,
        ForeignKey("qr_physical_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    action = Column(String(50), nullable=False)

    ip_address = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    document = relationship(
        "QRPhysicalDocument",
        back_populates="audit_logs",
        lazy="selectin",
    )

    __table_args__ = (
        Index(
            "idx_qr_physical_audit_doc_time",
            "document_id",
            "created_at",
        ),
    )


# =====================================================
# 📦 SUBMISSION STATUS ENUM
# =====================================================
class SubmissionStatus(enum.Enum):
    SUBMITTED = "SUBMITTED"
    RECEIVED = "RECEIVED"


# =====================================================
# 📤 QR PHYSICAL SUBMISSION
# =====================================================
class QRPhysicalSubmission(Base):
    __tablename__ = "qr_physical_submissions"

    id = Column(Integer, primary_key=True, index=True)

    qr_document_id = Column(
        Integer,
        ForeignKey("qr_physical_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    file_name = Column(String(255), nullable=False)
    submitted_to = Column(String(255), nullable=False)
    submitted_location = Column(String(255), nullable=False)
    remarks = Column(Text, nullable=True)

    submitted_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    received_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    status = Column(
        Enum(
            SubmissionStatus,
            name="submission_status_enum",  # PostgreSQL-safe enum name
        ),
        nullable=False,
        default=SubmissionStatus.SUBMITTED,
        index=True,
    )

    document = relationship(
        "QRPhysicalDocument",
        back_populates="submissions",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_qr_submission_status", "status"),
    )
