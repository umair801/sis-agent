"""
Communication portal API routes for AgAI_30 SIS.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_roles
from app.db.database import get_db
from app.schemas.auth import TokenPayload
from app.schemas.communication import (
    AnnouncementCreate, AnnouncementUpdate, AnnouncementResponse,
    MessageCreate, MessageResponse,
    NotificationLogResponse,
    NotificationPreferenceUpdate, NotificationPreferenceResponse,
    BulkNotifyRequest,
)
from app.services.communication_service import (
    AnnouncementService, MessageService,
    NotificationService, NotificationPreferenceService,
)

router = APIRouter(prefix="/communication", tags=["Communication"])

ADMIN_ROLES  = ["SuperAdmin", "DistrictAdmin", "Principal"]
STAFF_ROLES  = ["SuperAdmin", "DistrictAdmin", "Principal", "Teacher", "SpEdCoordinator"]
ALL_ROLES    = ["SuperAdmin", "DistrictAdmin", "Principal", "Teacher", "SpEdCoordinator", "Parent"]


# ===========================================================================
# Announcements
# ===========================================================================

@router.post("/announcements", response_model=AnnouncementResponse, status_code=201)
async def create_announcement(
    payload: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*STAFF_ROLES)),
):
    return await AnnouncementService.create_announcement(
        db, UUID(current_user.tenant_id), payload, UUID(current_user.sub)
    )


@router.get("/announcements", response_model=dict)
async def list_announcements(
    status_filter: Optional[str] = Query(None, alias="status"),
    audience: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ALL_ROLES)),
):
    anns, total = await AnnouncementService.list_announcements(
        db, UUID(current_user.tenant_id), status_filter, audience, skip, limit
    )
    return {
        "total": total,
        "data": [AnnouncementResponse.model_validate(a) for a in anns],
    }


@router.get("/announcements/{ann_id}", response_model=AnnouncementResponse)
async def get_announcement(
    ann_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ALL_ROLES)),
):
    ann = await AnnouncementService.get_announcement(
        db, UUID(current_user.tenant_id), ann_id
    )
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return ann


@router.patch("/announcements/{ann_id}", response_model=AnnouncementResponse)
async def update_announcement(
    ann_id: UUID,
    payload: AnnouncementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*STAFF_ROLES)),
):
    ann = await AnnouncementService.update_announcement(
        db, UUID(current_user.tenant_id), ann_id, payload
    )
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return ann


@router.delete("/announcements/{ann_id}", status_code=204)
async def delete_announcement(
    ann_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ADMIN_ROLES)),
):
    deleted = await AnnouncementService.delete_announcement(
        db, UUID(current_user.tenant_id), ann_id
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Announcement not found")


# ===========================================================================
# Notifications
# ===========================================================================

@router.post("/announcements/{ann_id}/notify", response_model=dict)
async def dispatch_notification(
    ann_id: UUID,
    payload: BulkNotifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*STAFF_ROLES)),
):
    payload.announcement_id = ann_id
    try:
        logs = await NotificationService.dispatch_announcement(
            db, UUID(current_user.tenant_id), payload, UUID(current_user.sub)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    sent     = sum(1 for l in logs if l.status in ("sent", "delivered"))
    failed   = sum(1 for l in logs if l.status == "failed")
    return {"total": len(logs), "sent": sent, "failed": failed}


@router.get("/notifications/logs", response_model=List[NotificationLogResponse])
async def get_notification_logs(
    announcement_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ADMIN_ROLES)),
):
    return await NotificationService.get_notification_logs(
        db, UUID(current_user.tenant_id), announcement_id, skip, limit
    )


# ===========================================================================
# Messages
# ===========================================================================

@router.post("/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    payload: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ALL_ROLES)),
):
    return await MessageService.send_message(
        db, UUID(current_user.tenant_id), UUID(current_user.sub), payload
    )


@router.get("/messages/inbox", response_model=dict)
async def get_inbox(
    unread_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ALL_ROLES)),
):
    msgs, total = await MessageService.list_inbox(
        db, UUID(current_user.tenant_id), UUID(current_user.sub), unread_only, skip, limit
    )
    return {
        "total": total,
        "data": [MessageResponse.model_validate(m) for m in msgs],
    }


@router.get("/messages/sent", response_model=dict)
async def get_sent(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ALL_ROLES)),
):
    msgs, total = await MessageService.list_sent(
        db, UUID(current_user.tenant_id), UUID(current_user.sub), skip, limit
    )
    return {
        "total": total,
        "data": [MessageResponse.model_validate(m) for m in msgs],
    }


@router.patch("/messages/{message_id}/read", response_model=MessageResponse)
async def mark_message_read(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ALL_ROLES)),
):
    msg = await MessageService.mark_read(
        db, UUID(current_user.tenant_id), message_id, UUID(current_user.sub)
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    return msg


@router.get("/messages/{message_id}/thread", response_model=List[MessageResponse])
async def get_thread(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ALL_ROLES)),
):
    return await MessageService.get_thread(
        db, UUID(current_user.tenant_id), message_id
    )


# ===========================================================================
# Notification Preferences
# ===========================================================================

@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ALL_ROLES)),
):
    return await NotificationPreferenceService.get_or_create(
        db, UUID(current_user.tenant_id), UUID(current_user.sub)
    )


@router.patch("/preferences", response_model=NotificationPreferenceResponse)
async def update_preferences(
    payload: NotificationPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ALL_ROLES)),
):
    return await NotificationPreferenceService.update_preferences(
        db, UUID(current_user.tenant_id), UUID(current_user.sub), payload
    )