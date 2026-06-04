"""
Communication portal models for AgAI_30 SIS.
Covers: announcements, messages, notification logs, notification preferences.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Text, Boolean, DateTime,
    ForeignKey, Integer, Index, UniqueConstraint
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship as sa_relationship
from sqlalchemy.sql import func

from app.db.database import Base


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class AnnouncementAudience(str, PyEnum):
    ALL            = "all"
    STAFF          = "staff"
    PARENTS        = "parents"
    STUDENTS       = "students"
    TEACHERS       = "teachers"
    ADMINS         = "admins"
    SPED_TEAM      = "sped_team"


class AnnouncementStatus(str, PyEnum):
    DRAFT       = "draft"
    PUBLISHED   = "published"
    ARCHIVED    = "archived"


class MessageStatus(str, PyEnum):
    SENT        = "sent"
    DELIVERED   = "delivered"
    READ        = "read"
    FAILED      = "failed"


class NotificationChannel(str, PyEnum):
    EMAIL   = "email"
    SMS     = "sms"
    IN_APP  = "in_app"


class NotificationStatus(str, PyEnum):
    PENDING     = "pending"
    SENT        = "sent"
    DELIVERED   = "delivered"
    FAILED      = "failed"
    BOUNCED     = "bounced"


# ---------------------------------------------------------------------------
# sis_announcement
# ---------------------------------------------------------------------------

class Announcement(Base):
    __tablename__ = "sis_announcement"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id    = Column(UUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    school_id    = Column(UUID(as_uuid=True), ForeignKey("sis_school.id", ondelete="SET NULL"), nullable=True)
    created_by   = Column(UUID(as_uuid=True), ForeignKey("sis_user.id", ondelete="SET NULL"), nullable=True)

    title        = Column(String(255), nullable=False)
    body         = Column(Text, nullable=False)
    audience     = Column(
        SAEnum(*[e.value for e in AnnouncementAudience], name="sis_announcement_audience", create_type=False),
        nullable=False,
        default=AnnouncementAudience.ALL.value,
    )
    status       = Column(
        SAEnum(*[e.value for e in AnnouncementStatus], name="sis_announcement_status", create_type=False),
        nullable=False,
        default=AnnouncementStatus.DRAFT.value,
    )
    is_urgent    = Column(Boolean, nullable=False, default=False)
    publish_at   = Column(DateTime(timezone=True), nullable=True)   # scheduled publish time
    expires_at   = Column(DateTime(timezone=True), nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    notifications = sa_relationship("NotificationLog", back_populates="announcement", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sis_announcement_tenant_status", "tenant_id", "status"),
        Index("ix_sis_announcement_audience", "audience"),
    )


# ---------------------------------------------------------------------------
# sis_message  (direct messages between users, e.g. teacher <-> parent)
# ---------------------------------------------------------------------------

class Message(Base):
    __tablename__ = "sis_message"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id    = Column(UUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    sender_id    = Column(UUID(as_uuid=True), ForeignKey("sis_user.id", ondelete="SET NULL"), nullable=True)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("sis_user.id", ondelete="SET NULL"), nullable=True)
    student_id   = Column(UUID(as_uuid=True), ForeignKey("sis_student.id", ondelete="SET NULL"), nullable=True)

    subject      = Column(String(255), nullable=True)
    body         = Column(Text, nullable=False)
    status       = Column(
        SAEnum(*[e.value for e in MessageStatus], name="sis_message_status", create_type=False),
        nullable=False,
        default=MessageStatus.SENT.value,
    )
    is_read      = Column(Boolean, nullable=False, default=False)
    read_at      = Column(DateTime(timezone=True), nullable=True)
    parent_message_id = Column(UUID(as_uuid=True), ForeignKey("sis_message.id", ondelete="SET NULL"), nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    sender       = sa_relationship("User", foreign_keys=[sender_id])
    recipient    = sa_relationship("User", foreign_keys=[recipient_id])
    student      = sa_relationship("Student", foreign_keys=[student_id])
    replies      = sa_relationship("Message", foreign_keys=[parent_message_id])

    __table_args__ = (
        Index("ix_sis_message_recipient", "recipient_id", "is_read"),
        Index("ix_sis_message_tenant_sender", "tenant_id", "sender_id"),
        Index("ix_sis_message_student", "student_id"),
    )


# ---------------------------------------------------------------------------
# sis_notification_log  (outbound email/SMS delivery records)
# ---------------------------------------------------------------------------

class NotificationLog(Base):
    __tablename__ = "sis_notification_log"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id        = Column(UUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    announcement_id  = Column(UUID(as_uuid=True), ForeignKey("sis_announcement.id", ondelete="SET NULL"), nullable=True)
    recipient_user_id = Column(UUID(as_uuid=True), ForeignKey("sis_user.id", ondelete="SET NULL"), nullable=True)

    channel          = Column(
        SAEnum(*[e.value for e in NotificationChannel], name="sis_notification_channel", create_type=False),
        nullable=False,
    )
    status           = Column(
        SAEnum(*[e.value for e in NotificationStatus], name="sis_notification_status", create_type=False),
        nullable=False,
        default=NotificationStatus.PENDING.value,
    )
    recipient_email  = Column(String(255), nullable=True)
    recipient_phone  = Column(String(50), nullable=True)
    subject          = Column(String(255), nullable=True)
    body_preview     = Column(String(500), nullable=True)   # first 500 chars for audit
    external_id      = Column(String(255), nullable=True)   # Twilio SID or email provider ID
    error_message    = Column(Text, nullable=True)
    sent_at          = Column(DateTime(timezone=True), nullable=True)
    delivered_at     = Column(DateTime(timezone=True), nullable=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())

    announcement     = sa_relationship("Announcement", back_populates="notifications")

    __table_args__ = (
        Index("ix_sis_notification_log_tenant", "tenant_id", "status"),
        Index("ix_sis_notification_log_announcement", "announcement_id"),
    )


# ---------------------------------------------------------------------------
# sis_notification_preference  (per-user channel preferences)
# ---------------------------------------------------------------------------

class NotificationPreference(Base):
    __tablename__ = "sis_notification_preference"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id    = Column(UUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    user_id      = Column(UUID(as_uuid=True), ForeignKey("sis_user.id", ondelete="CASCADE"), nullable=False)

    email_enabled    = Column(Boolean, nullable=False, default=True)
    sms_enabled      = Column(Boolean, nullable=False, default=False)
    in_app_enabled   = Column(Boolean, nullable=False, default=True)
    urgent_sms       = Column(Boolean, nullable=False, default=True)   # always SMS for urgent
    phone_number     = Column(String(50), nullable=True)               # override for SMS

    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_sis_notif_pref_user"),
    )