"""
Communication service layer for AgAI_30 SIS.
Handles announcements, messages, notification dispatch (email + SMS).
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Announcement, Message, NotificationLog, NotificationPreference, User
from app.models.communication import NotificationChannel, NotificationStatus
from app.schemas.communication import (
    AnnouncementCreate, AnnouncementUpdate,
    MessageCreate,
    NotificationPreferenceUpdate,
    BulkNotifyRequest,
)
from app.core.logging import logger


# ---------------------------------------------------------------------------
# Announcements
# ---------------------------------------------------------------------------

class AnnouncementService:

    @staticmethod
    async def create_announcement(
        db: AsyncSession,
        tenant_id: UUID,
        payload: AnnouncementCreate,
        created_by: UUID,
    ) -> Announcement:
        ann = Announcement(
            tenant_id=tenant_id,
            created_by=created_by,
            **payload.model_dump(),
        )
        db.add(ann)
        await db.commit()
        await db.refresh(ann)
        return ann

    @staticmethod
    async def list_announcements(
        db: AsyncSession,
        tenant_id: UUID,
        status: Optional[str] = None,
        audience: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Announcement], int]:
        query = select(Announcement).where(Announcement.tenant_id == tenant_id)
        if status:
            query = query.where(Announcement.status == status)
        if audience:
            query = query.where(Announcement.audience == audience)

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        result = await db.execute(
            query.order_by(Announcement.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def get_announcement(
        db: AsyncSession,
        tenant_id: UUID,
        ann_id: UUID,
    ) -> Optional[Announcement]:
        result = await db.execute(
            select(Announcement).where(
                Announcement.id == ann_id,
                Announcement.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_announcement(
        db: AsyncSession,
        tenant_id: UUID,
        ann_id: UUID,
        payload: AnnouncementUpdate,
    ) -> Optional[Announcement]:
        result = await db.execute(
            select(Announcement).where(
                Announcement.id == ann_id,
                Announcement.tenant_id == tenant_id,
            )
        )
        ann = result.scalar_one_or_none()
        if not ann:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(ann, field, value)
        await db.commit()
        await db.refresh(ann)
        return ann

    @staticmethod
    async def delete_announcement(
        db: AsyncSession,
        tenant_id: UUID,
        ann_id: UUID,
    ) -> bool:
        result = await db.execute(
            select(Announcement).where(
                Announcement.id == ann_id,
                Announcement.tenant_id == tenant_id,
            )
        )
        ann = result.scalar_one_or_none()
        if not ann:
            return False
        await db.delete(ann)
        await db.commit()
        return True


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

class MessageService:

    @staticmethod
    async def send_message(
        db: AsyncSession,
        tenant_id: UUID,
        sender_id: UUID,
        payload: MessageCreate,
    ) -> Message:
        msg = Message(
            tenant_id=tenant_id,
            sender_id=sender_id,
            **payload.model_dump(),
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg

    @staticmethod
    async def list_inbox(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Message], int]:
        query = select(Message).where(
            Message.tenant_id == tenant_id,
            Message.recipient_id == user_id,
        )
        if unread_only:
            query = query.where(Message.is_read == False)

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        result = await db.execute(
            query.order_by(Message.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def list_sent(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Message], int]:
        query = select(Message).where(
            Message.tenant_id == tenant_id,
            Message.sender_id == user_id,
        )
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()
        result = await db.execute(
            query.order_by(Message.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def mark_read(
        db: AsyncSession,
        tenant_id: UUID,
        message_id: UUID,
        user_id: UUID,
    ) -> Optional[Message]:
        result = await db.execute(
            select(Message).where(
                Message.id == message_id,
                Message.tenant_id == tenant_id,
                Message.recipient_id == user_id,
            )
        )
        msg = result.scalar_one_or_none()
        if not msg:
            return None
        msg.is_read = True
        msg.read_at = datetime.now(timezone.utc)
        msg.status = "read"
        await db.commit()
        await db.refresh(msg)
        return msg

    @staticmethod
    async def get_thread(
        db: AsyncSession,
        tenant_id: UUID,
        message_id: UUID,
    ) -> List[Message]:
        result = await db.execute(
            select(Message).where(
                Message.tenant_id == tenant_id,
                Message.parent_message_id == message_id,
            ).order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Notification dispatch (email stub + Twilio SMS stub)
# ---------------------------------------------------------------------------

class NotificationService:

    @staticmethod
    async def dispatch_announcement(
        db: AsyncSession,
        tenant_id: UUID,
        request: BulkNotifyRequest,
        dispatched_by: UUID,
    ) -> List[NotificationLog]:
        """
        Fetch announcement, resolve recipients by audience,
        create NotificationLog entries and attempt delivery.

        Email: uses configured SMTP (stub — logs only if not configured).
        SMS:   uses Twilio (stub — logs only if credentials not configured).
        """
        ann_result = await db.execute(
            select(Announcement).where(
                Announcement.id == request.announcement_id,
                Announcement.tenant_id == tenant_id,
            )
        )
        ann = ann_result.scalar_one_or_none()
        if not ann:
            raise ValueError("Announcement not found")

        # Resolve recipients based on audience
        recipients = await NotificationService._resolve_recipients(
            db, tenant_id, ann.audience
        )

        logs = []
        for user in recipients:
            for channel in request.channels:
                log = NotificationLog(
                    tenant_id=tenant_id,
                    announcement_id=ann.id,
                    recipient_user_id=user.id,
                    channel=channel.value,
                    status=NotificationStatus.PENDING.value,
                    recipient_email=user.email,
                    subject=ann.title,
                    body_preview=ann.body[:500],
                )
                db.add(log)
                logs.append(log)

        await db.flush()

        # Attempt delivery for each log
        for log in logs:
            try:
                if log.channel == NotificationChannel.EMAIL.value:
                    await NotificationService._send_email(log, ann)
                elif log.channel == NotificationChannel.SMS.value:
                    await NotificationService._send_sms(log, ann)
                else:
                    # in_app: mark delivered immediately
                    log.status = NotificationStatus.DELIVERED.value
                    log.delivered_at = datetime.now(timezone.utc)
            except Exception as e:
                log.status = NotificationStatus.FAILED.value
                log.error_message = str(e)
                logger.warning("Notification delivery failed", error=str(e))

        await db.commit()
        return logs

    @staticmethod
    async def _resolve_recipients(
        db: AsyncSession,
        tenant_id: UUID,
        audience: str,
    ) -> List[User]:
        """Return users matching the audience filter."""
        from app.models import Role
        query = select(User).where(
            User.tenant_id == tenant_id,
            User.is_active == True,
        )
        # Filter by role name for non-"all" audiences
        audience_role_map = {
            "staff":    ["Teacher", "Principal", "SpEdCoordinator", "DistrictAdmin", "SuperAdmin"],
            "teachers": ["Teacher"],
            "admins":   ["SuperAdmin", "DistrictAdmin", "Principal"],
            "sped_team":["SpEdCoordinator", "Teacher"],
            "parents":  ["Parent"],
        }
        if audience in audience_role_map:
            role_names = audience_role_map[audience]
            roles_result = await db.execute(
                select(Role.id).where(
                    Role.tenant_id == tenant_id,
                    Role.name.in_(role_names),
                )
            )
            role_ids = [r[0] for r in roles_result.all()]
            if role_ids:
                query = query.where(User.role_id.in_(role_ids))
            else:
                return []

        result = await db.execute(query.limit(500))
        return list(result.scalars().all())

    @staticmethod
    async def _send_email(log: NotificationLog, ann: Announcement) -> None:
        """
        Email delivery stub.
        In production: replace with SendGrid / AWS SES / SMTP call.
        """
        import os
        smtp_host = os.getenv("SMTP_HOST", "")
        if not smtp_host:
            # No SMTP configured — mark as sent for demo purposes
            log.status = NotificationStatus.SENT.value
            log.sent_at = datetime.now(timezone.utc)
            logger.info(
                "Email stub: would send",
                to=log.recipient_email,
                subject=log.subject,
            )
            return
        # TODO: plug in real SMTP/SendGrid here
        log.status = NotificationStatus.SENT.value
        log.sent_at = datetime.now(timezone.utc)

    @staticmethod
    async def _send_sms(log: NotificationLog, ann: Announcement) -> None:
        """
        Twilio SMS stub.
        In production: install twilio, set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
        TWILIO_FROM_NUMBER in .env.
        """
        import os
        account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        auth_token  = os.getenv("TWILIO_AUTH_TOKEN", "")
        from_number = os.getenv("TWILIO_FROM_NUMBER", "")

        if not all([account_sid, auth_token, from_number, log.recipient_phone]):
            log.status = NotificationStatus.SENT.value
            log.sent_at = datetime.now(timezone.utc)
            logger.info(
                "SMS stub: would send",
                to=log.recipient_phone,
                body=ann.body[:160],
            )
            return

        try:
            from twilio.rest import Client
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                body=f"{ann.title}: {ann.body[:140]}",
                from_=from_number,
                to=log.recipient_phone,
            )
            log.status = NotificationStatus.SENT.value
            log.external_id = message.sid
            log.sent_at = datetime.now(timezone.utc)
        except Exception as e:
            raise e

    @staticmethod
    async def get_notification_logs(
        db: AsyncSession,
        tenant_id: UUID,
        announcement_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[NotificationLog]:
        query = select(NotificationLog).where(
            NotificationLog.tenant_id == tenant_id
        )
        if announcement_id:
            query = query.where(NotificationLog.announcement_id == announcement_id)
        result = await db.execute(
            query.order_by(NotificationLog.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Notification Preferences
# ---------------------------------------------------------------------------

class NotificationPreferenceService:

    @staticmethod
    async def get_or_create(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
    ) -> NotificationPreference:
        result = await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.tenant_id == tenant_id,
                NotificationPreference.user_id == user_id,
            )
        )
        pref = result.scalar_one_or_none()
        if not pref:
            pref = NotificationPreference(tenant_id=tenant_id, user_id=user_id)
            db.add(pref)
            await db.commit()
            await db.refresh(pref)
        return pref

    @staticmethod
    async def update_preferences(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        payload: NotificationPreferenceUpdate,
    ) -> NotificationPreference:
        pref = await NotificationPreferenceService.get_or_create(db, tenant_id, user_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(pref, field, value)
        await db.commit()
        await db.refresh(pref)
        return pref