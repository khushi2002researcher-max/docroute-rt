from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    TIMESTAMP,
    ForeignKey,
    Boolean,
    CheckConstraint,
    UniqueConstraint,
    Index,
    event,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime, timezone
from app.database import Base
from app.auth.models import User


# =====================================================
# DOCUMENT (TRACKED DOCUMENT)
# =====================================================

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    tracking_id = Column(String(20), unique=True, nullable=False)

    file_name = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    stored_file_name = Column(String, nullable=False)
    content = Column(Text)

    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    last_updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    last_viewed_at = Column(TIMESTAMP(timezone=True))
    last_viewed_by = Column(Integer, ForeignKey("users.id"))

    is_deleted = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("idx_tracking_id", "tracking_id"),
        Index("idx_document_deleted", "is_deleted"),
    )

    # ================= RELATIONSHIPS =================

    owner = relationship(
        "User",
        foreign_keys=[owner_id],
        back_populates="documents",
    )

    last_viewed_user = relationship(
        "User",
        foreign_keys=[last_viewed_by],
    )

    versions = relationship(
        "DocumentVersion",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentVersion.version_number",
    )

    audit_logs = relationship(
        "AuditLog",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    access_list = relationship(
        "DocumentAccess",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    live_viewers = relationship(
        "DocumentLiveViewer",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    share_links = relationship(
        "DocumentShareLink",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    download_logs = relationship(
        "DocumentDownloadLog",
        back_populates="document",
        cascade="all, delete-orphan",
    )


@event.listens_for(Document, "before_update", propagate=True)
def update_last_updated(mapper, connection, target):
    target.last_updated_at = datetime.now(timezone.utc)


# =====================================================
# DOCUMENT VERSION (WITH DIFF SUPPORT)
# =====================================================

class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True)

    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )

    version_number = Column(Integer, nullable=False)
    content = Column(Text)
    diff = Column(Text)

    stored_file_name = Column(String)
    summary = Column(Text)
    tags = Column(ARRAY(String))

    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_document_version"),
        Index("idx_document_versions_doc", "document_id"),
    )

    document = relationship("Document", back_populates="versions")
    created_by_user = relationship("User", foreign_keys=[created_by])


# =====================================================
# DOCUMENT ACCESS (PER-USER PERMISSIONS)
# =====================================================

class DocumentAccess(Base):
    __tablename__ = "document_access"

    id = Column(Integer, primary_key=True)

    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    permission = Column(String(10), nullable=False)  # view | edit

    granted_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    granted_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    revoked_at = Column(TIMESTAMP(timezone=True))

    __table_args__ = (
        CheckConstraint("permission IN ('view','edit')", name="ck_doc_permission"),
        UniqueConstraint("document_id", "user_id", name="uq_doc_user_access"),
        Index("idx_access_document", "document_id"),
        Index("idx_access_user", "user_id"),
    )

    document = relationship("Document", back_populates="access_list")
    user = relationship("User", foreign_keys=[user_id])
    granted_by_user = relationship("User", foreign_keys=[granted_by])


# =====================================================
# AUDIT LOG (FULL TRACKING)
# =====================================================

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)

    module = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    event_type = Column(String(30), index=True)

    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )

    performed_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )

    extra_data = Column(Text)
    client_info = Column(Text)

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    document = relationship("Document", back_populates="audit_logs")
    performed_by_user = relationship("User", foreign_keys=[performed_by])


# =====================================================
# LIVE VIEWERS
# =====================================================

class DocumentLiveViewer(Base):
    __tablename__ = "document_live_viewers"

    id = Column(Integer, primary_key=True)

    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )

    last_ping_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    document = relationship("Document", back_populates="live_viewers")
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_live_doc", "document_id"),
        Index("idx_live_user", "user_id"),
    )


# =====================================================
# EXPIRING SHARE LINKS (LINK + QR)
# =====================================================

class DocumentShareLink(Base):
    __tablename__ = "document_share_links"

    id = Column(Integer, primary_key=True)

    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )

    token = Column(String(64), unique=True, index=True, nullable=False)

    share_mode = Column(
        String(10),
        nullable=False,
        default="link",  # link | qr
    )

    permission = Column(String(10), nullable=False, default="view")
    password_hash = Column(String)

    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    expires_at = Column(TIMESTAMP(timezone=True), index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    revoked_at = Column(TIMESTAMP(timezone=True))

    opened_count = Column(Integer, default=0, nullable=False)
    last_opened_at = Column(TIMESTAMP(timezone=True))

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    document = relationship("Document", back_populates="share_links")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        CheckConstraint(
            "permission IN ('view','edit','download')",
            name="ck_share_permission",
        ),
        CheckConstraint(
            "share_mode IN ('link','qr')",
            name="ck_share_mode",
        ),
        Index("idx_share_token", "token"),
    )


# =====================================================
# DOWNLOAD TRACKING
# =====================================================

class DocumentDownloadLog(Base):
    __tablename__ = "document_download_logs"

    id = Column(Integer, primary_key=True)

    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )

    downloaded_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )

    format = Column(String(10), nullable=False)  # pdf | docx

    downloaded_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    client_info = Column(Text)

    document = relationship("Document", back_populates="download_logs")
    user = relationship("User", foreign_keys=[downloaded_by])
