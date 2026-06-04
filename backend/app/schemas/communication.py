"""
Pydantic schemas for Communication portal.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.communication import (
    AnnouncementAudience, AnnouncementStatus,
    MessageStatus, NotificationChannel, NotificationStatus,
)


# ===========================================================================
# Announcement
# ===========================================================================

class AnnouncementCreate(BaseModel):
    title: str
    body: str
    audience: AnnouncementAudience = AnnouncementAudience.ALL
    status: AnnouncementStatus = AnnouncementStatus.DRAFT
    is_urgent: bool = False
    publish_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    school_id: Optional[UUID] = None


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    audience: Optional[AnnouncementAudience] = None
    status: Optional[AnnouncementStatus] = None
    is_urgent: Optional[bool] = None
    publish_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class AnnouncementResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    school_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    title: str
    body: str
    audience: str
    status: str
    is_urgent: bool
    publish_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ===========================================================================
# Message
# ===========================================================================

class MessageCreate(BaseModel):
    recipient_id: UUID
    student_id: Optional[UUID] = None
    subject: Optional[str] = None
    body: str
    parent_message_id: Optional[UUID] = None


class MessageResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    sender_id: Optional[UUID] = None
    recipient_id: Optional[UUID] = None
    student_id: Optional[UUID] = None
    subject: Optional[str] = None
    body: str
    status: str
    is_read: bool
    read_at: Optional[datetime] = None
    parent_message_id: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ===========================================================================
# NotificationLog
# ===========================================================================

class NotificationLogResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    announcement_id: Optional[UUID] = None
    recipient_user_id: Optional[UUID] = None
    channel: str
    status: str
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    subject: Optional[str] = None
    body_preview: Optional[str] = None
    external_id: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ===========================================================================
# NotificationPreference
# ===========================================================================

class NotificationPreferenceUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    urgent_sms: Optional[bool] = None
    phone_number: Optional[str] = None


class NotificationPreferenceResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    email_enabled: bool
    sms_enabled: bool
    in_app_enabled: bool
    urgent_sms: bool
    phone_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ===========================================================================
# Bulk notification request
# ===========================================================================

class BulkNotifyRequest(BaseModel):
    announcement_id: UUID
    channels: List[NotificationChannel] = [NotificationChannel.EMAIL]