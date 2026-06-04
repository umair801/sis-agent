"""
SpEd/IEP API routes for AgAI_30 SIS.
All endpoints are tenant-scoped via JWT claims.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_roles
from app.db.database import get_db
from app.models.sped_enums import IEPStatus
from app.schemas.auth import TokenPayload
from app.schemas.sped import (
    IEPCreate, IEPUpdate, IEPResponse, IEPSummary, IEPDeadlineAlert,
    IEPServiceCreate, IEPServiceUpdate, IEPServiceResponse,
    IEPGoalCreate, IEPGoalUpdate, IEPGoalResponse,
    IEPGoalProgressCreate, IEPGoalProgressResponse,
    IEPAccommodationCreate, IEPAccommodationUpdate, IEPAccommodationResponse,
    IEPTeamMemberCreate, IEPTeamMemberUpdate, IEPTeamMemberResponse,
    IEPMeetingCreate, IEPMeetingUpdate, IEPMeetingResponse,
)
from app.services.sped_service import (
    SpEdService,
    IEPServiceCRUD,
    IEPGoalCRUD,
    IEPAccommodationCRUD,
    IEPTeamMemberCRUD,
    IEPMeetingCRUD,
    IEPComplianceService,
)

router = APIRouter(prefix="/sped", tags=["SpEd / IEP"])

# Role constants
SPED_WRITE_ROLES = ["SuperAdmin", "DistrictAdmin", "Principal", "SpEdCoordinator"]
SPED_READ_ROLES  = ["SuperAdmin", "DistrictAdmin", "Principal", "SpEdCoordinator", "Teacher"]
ADMIN_ROLES      = ["SuperAdmin", "DistrictAdmin"]


# ===========================================================================
# IEP — master record
# ===========================================================================

@router.post("/ieps", response_model=IEPResponse, status_code=status.HTTP_201_CREATED)
async def create_iep(
    payload: IEPCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_WRITE_ROLES)),
):
    try:
        return await SpEdService.create_iep(
            db,
            tenant_id=UUID(current_user.tenant_id),
            payload=payload,
            created_by=UUID(current_user.sub),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/ieps", response_model=dict)
async def list_ieps(
    status_filter: Optional[IEPStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_READ_ROLES)),
):
    ieps, total = await SpEdService.list_ieps(
        db,
        tenant_id=UUID(current_user.tenant_id),
        status=status_filter,
        skip=skip,
        limit=limit,
    )
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [IEPSummary.model_validate(i) for i in ieps],
    }


@router.get("/ieps/student/{student_id}", response_model=List[IEPSummary])
async def list_ieps_for_student(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_READ_ROLES)),
):
    ieps = await SpEdService.list_ieps_for_student(
        db,
        tenant_id=UUID(current_user.tenant_id),
        student_id=student_id,
    )
    return [IEPSummary.model_validate(i) for i in ieps]


@router.get("/ieps/{iep_id}", response_model=IEPResponse)
async def get_iep(
    iep_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_READ_ROLES)),
):
    iep = await SpEdService.get_iep(
        db,
        tenant_id=UUID(current_user.tenant_id),
        iep_id=iep_id,
    )
    if not iep:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IEP not found")
    return iep


@router.patch("/ieps/{iep_id}", response_model=IEPResponse)
async def update_iep(
    iep_id: UUID,
    payload: IEPUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_WRITE_ROLES)),
):
    iep = await SpEdService.update_iep(
        db,
        tenant_id=UUID(current_user.tenant_id),
        iep_id=iep_id,
        payload=payload,
        updated_by=UUID(current_user.sub),
    )
    if not iep:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IEP not found")
    return iep


@router.delete("/ieps/{iep_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_iep(
    iep_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ADMIN_ROLES)),
):
    try:
        deleted = await SpEdService.delete_iep(
            db,
            tenant_id=UUID(current_user.tenant_id),
            iep_id=iep_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IEP not found")


# ===========================================================================
# Services (OT, speech, etc.)
# ===========================================================================

@router.post("/ieps/{iep_id}/services", response_model=IEPServiceResponse, status_code=status.HTTP_201_CREATED)
async def add_service(
    iep_id: UUID,
    payload: IEPServiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_WRITE_ROLES)),
):
    return await IEPServiceCRUD.add_service(
        db,
        tenant_id=UUID(current_user.tenant_id),
        iep_id=iep_id,
        payload=payload,
    )


@router.patch("/services/{service_id}", response_model=IEPServiceResponse)
async def update_service(
    service_id: UUID,
    payload: IEPServiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_WRITE_ROLES)),
):
    svc = await IEPServiceCRUD.update_service(
        db,
        tenant_id=UUID(current_user.tenant_id),
        service_id=service_id,
        payload=payload,
    )
    if not svc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return svc


@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_WRITE_ROLES)),
):
    deleted = await IEPServiceCRUD.delete_service(
        db,
        tenant_id=UUID(current_user.tenant_id),
        service_id=service_id,
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")


# ===========================================================================
# Goals
# ===========================================================================

@router.post("/ieps/{iep_id}/goals", response_model=IEPGoalResponse, status_code=status.HTTP_201_CREATED)
async def add_goal(
    iep_id: UUID,
    payload: IEPGoalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_WRITE_ROLES)),
):
    goal = await IEPGoalCRUD.add_goal(
        db,
        tenant_id=UUID(current_user.tenant_id),
        iep_id=iep_id,
        payload=payload,
    )
    return IEPGoalResponse.model_validate(goal)


@router.patch("/goals/{goal_id}", response_model=IEPGoalResponse)
async def update_goal(
    goal_id: UUID,
    payload: IEPGoalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_WRITE_ROLES)),
):
    goal = await IEPGoalCRUD.update_goal(
        db,
        tenant_id=UUID(current_user.tenant_id),
        goal_id=goal_id,
        payload=payload,
    )
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return IEPGoalResponse.model_validate(goal)


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_WRITE_ROLES)),
):
    deleted = await IEPGoalCRUD.delete_goal(
        db,
        tenant_id=UUID(current_user.tenant_id),
        goal_id=goal_id,
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")


# Goal progress notes
@router.post("/goals/{goal_id}/progress", response_model=IEPGoalProgressResponse, status_code=status.HTTP_201_CREATED)
async def add_progress_note(
    goal_id: UUID,
    payload: IEPGoalProgressCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_READ_ROLES)),
):
    return await IEPGoalCRUD.add_progress_note(
        db,
        tenant_id=UUID(current_user.tenant_id),
        goal_id=goal_id,
        payload=payload,
        recorded_by=UUID(current_user.sub),
    )


# ===========================================================================
# Accommodations
# ===========================================================================

@router.post("/ieps/{iep_id}/accommodations", response_model=IEPAccommodationResponse, status_code=status.HTTP_201_CREATED)
async def add_accommodation(
    iep_id: UUID,
    payload: IEPAccommodationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_WRITE_ROLES)),
):
    return await IEPAccommodationCRUD.add_accommodation(
        db,
        tenant_id=UUID(current_user.tenant_id),
        iep_id=iep_id,
        payload=payload,
    )


@router.patch("/accommodations/{accommodation_id}", response_model=IEPAccommodationResponse)
async def update_accommodation(
    accommodation_id: UUID,
    payload: IEPAccommodationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_WRITE_ROLES)),
):
    acc = await IEPAccommodationCRUD.update_accommodation(
        db,
        tenant_id=UUID(current_user.tenant_id),
        accommodation_id=accommodation_id,
        payload=payload,
    )
    if not acc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accommodation not found")
    return acc


@router.delete("/accommodations/{accommodation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_accommodation(
    accommodation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_WRITE_ROLES)),
):
    deleted = await IEPAccommodationCRUD.delete_accommodation(
        db,
        tenant_id=UUID(current_user.tenant_id),
        accommodation_id=accommodation_id,
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accommodation not found")


# ===========================================================================
# Team Members
# ===========================================================================

@router.post("/ieps/{iep_id}/team-members", response_model=IEPTeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_team_member(
    iep_id: UUID,
    payload: IEPTeamMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_WRITE_ROLES)),
):
    try:
        return await IEPTeamMemberCRUD.add_team_member(
            db,
            tenant_id=UUID(current_user.tenant_id),
            iep_id=iep_id,
            payload=payload,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.patch("/team-members/{member_id}", response_model=IEPTeamMemberResponse)
async def update_team_member(
    member_id: UUID,
    payload: IEPTeamMemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_WRITE_ROLES)),
):
    member = await IEPTeamMemberCRUD.update_team_member(
        db,
        tenant_id=UUID(current_user.tenant_id),
        member_id=member_id,
        payload=payload,
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found")
    return member


@router.delete("/team-members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team_member(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_WRITE_ROLES)),
):
    deleted = await IEPTeamMemberCRUD.delete_team_member(
        db,
        tenant_id=UUID(current_user.tenant_id),
        member_id=member_id,
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found")


# ===========================================================================
# Meetings
# ===========================================================================

@router.post("/ieps/{iep_id}/meetings", response_model=IEPMeetingResponse, status_code=status.HTTP_201_CREATED)
async def add_meeting(
    iep_id: UUID,
    payload: IEPMeetingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_WRITE_ROLES)),
):
    return await IEPMeetingCRUD.add_meeting(
        db,
        tenant_id=UUID(current_user.tenant_id),
        iep_id=iep_id,
        payload=payload,
        scheduled_by=UUID(current_user.sub),
    )


@router.patch("/meetings/{meeting_id}", response_model=IEPMeetingResponse)
async def update_meeting(
    meeting_id: UUID,
    payload: IEPMeetingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_WRITE_ROLES)),
):
    meeting = await IEPMeetingCRUD.update_meeting(
        db,
        tenant_id=UUID(current_user.tenant_id),
        meeting_id=meeting_id,
        payload=payload,
    )
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return meeting


@router.delete("/meetings/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_WRITE_ROLES)),
):
    deleted = await IEPMeetingCRUD.delete_meeting(
        db,
        tenant_id=UUID(current_user.tenant_id),
        meeting_id=meeting_id,
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")


# ===========================================================================
# Compliance / Deadline Alerts
# ===========================================================================

@router.get("/compliance/alerts", response_model=List[IEPDeadlineAlert])
async def get_compliance_alerts(
    within_days: int = Query(60, ge=1, le=365, description="Look-ahead window in days"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_READ_ROLES)),
):
    """
    Returns deadline alerts for all active IEPs:
    annual reviews, IEP expiry, and triennial re-evaluations.
    Sorted by severity (critical first) then soonest deadline.
    """
    return await IEPComplianceService.get_deadline_alerts(
        db,
        tenant_id=UUID(current_user.tenant_id),
        within_days=within_days,
    )


@router.get("/compliance/overdue", response_model=List[IEPSummary])
async def get_overdue_ieps(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*SPED_READ_ROLES)),
):
    """Returns all active IEPs whose end_date has already passed."""
    ieps = await IEPComplianceService.get_overdue_ieps(
        db,
        tenant_id=UUID(current_user.tenant_id),
    )
    return [IEPSummary.model_validate(i) for i in ieps]
