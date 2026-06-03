"""
SpEd/IEP service layer for AgAI_30 SIS.
Handles all database operations for IEP records, services, goals,
accommodations, team members, meetings, and compliance deadline checks.
"""

from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    IEP, IEPService, IEPGoal, IEPGoalProgress,
    IEPAccommodation, IEPTeamMember, IEPMeeting,
    Student,
)
from app.models.sped_enums import IEPStatus
from app.schemas.sped import (
    IEPCreate, IEPUpdate,
    IEPServiceCreate, IEPServiceUpdate,
    IEPGoalCreate, IEPGoalUpdate,
    IEPGoalProgressCreate,
    IEPAccommodationCreate, IEPAccommodationUpdate,
    IEPTeamMemberCreate, IEPTeamMemberUpdate,
    IEPMeetingCreate, IEPMeetingUpdate,
    IEPDeadlineAlert,
)
from app.core.logging import logger


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iep_load_options():
    """Eager-load all nested collections in one query."""
    return [
        selectinload(IEP.services),
        selectinload(IEP.goals).selectinload(IEPGoal.progress_notes),
        selectinload(IEP.accommodations),
        selectinload(IEP.team_members),
        selectinload(IEP.meetings),
    ]


# ---------------------------------------------------------------------------
# IEP CRUD
# ---------------------------------------------------------------------------

class SpEdService:

    # ------------------------------------------------------------------
    # Create IEP (with optional nested records)
    # ------------------------------------------------------------------

    @staticmethod
    async def create_iep(
        db: AsyncSession,
        tenant_id: UUID,
        payload: IEPCreate,
        created_by: UUID,
    ) -> IEP:
        # Validate student belongs to tenant
        student = await db.get(Student, payload.student_id)
        if not student or student.tenant_id != tenant_id:
            raise ValueError("Student not found in this district")

        # Check for existing active IEP for same student
        existing = await db.execute(
            select(IEP).where(
                IEP.tenant_id == tenant_id,
                IEP.student_id == payload.student_id,
                IEP.status == IEPStatus.ACTIVE,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(
                "Student already has an active IEP. "
                "Revoke or expire the existing IEP before creating a new one."
            )

        # Create master IEP record
        iep_data = payload.model_dump(exclude={"services", "goals", "accommodations", "team_members"})
        iep = IEP(
            tenant_id=tenant_id,
            created_by=created_by,
            updated_by=created_by,
            **iep_data,
        )
        db.add(iep)
        await db.flush()  # get iep.id before inserting children

        # Create nested services
        for svc in payload.services:
            db.add(IEPService(
                tenant_id=tenant_id,
                iep_id=iep.id,
                **svc.model_dump(),
            ))

        # Create nested goals
        for goal in payload.goals:
            db.add(IEPGoal(
                tenant_id=tenant_id,
                iep_id=iep.id,
                **goal.model_dump(),
            ))

        # Create nested accommodations
        for acc in payload.accommodations:
            db.add(IEPAccommodation(
                tenant_id=tenant_id,
                iep_id=iep.id,
                **acc.model_dump(),
            ))

        # Create nested team members
        for member in payload.team_members:
            db.add(IEPTeamMember(
                tenant_id=tenant_id,
                iep_id=iep.id,
                **member.model_dump(),
            ))

        await db.commit()

        # Re-fetch with all relationships loaded
        result = await db.execute(
            select(IEP)
            .where(IEP.id == iep.id)
            .options(*_iep_load_options())
        )
        return result.scalar_one()

    # ------------------------------------------------------------------
    # Get single IEP (full detail)
    # ------------------------------------------------------------------

    @staticmethod
    async def get_iep(
        db: AsyncSession,
        tenant_id: UUID,
        iep_id: UUID,
    ) -> Optional[IEP]:
        result = await db.execute(
            select(IEP)
            .where(IEP.id == iep_id, IEP.tenant_id == tenant_id)
            .options(*_iep_load_options())
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # List IEPs for a student
    # ------------------------------------------------------------------

    @staticmethod
    async def list_ieps_for_student(
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID,
    ) -> List[IEP]:
        result = await db.execute(
            select(IEP)
            .where(IEP.tenant_id == tenant_id, IEP.student_id == student_id)
            .order_by(IEP.start_date.desc())
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # List all IEPs for tenant (summary, paginated)
    # ------------------------------------------------------------------

    @staticmethod
    async def list_ieps(
        db: AsyncSession,
        tenant_id: UUID,
        status: Optional[IEPStatus] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[IEP], int]:
        query = select(IEP).where(IEP.tenant_id == tenant_id)
        if status:
            query = query.where(IEP.status == status)

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        result = await db.execute(
            query.order_by(IEP.next_review_date.asc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    # ------------------------------------------------------------------
    # Update IEP
    # ------------------------------------------------------------------

    @staticmethod
    async def update_iep(
        db: AsyncSession,
        tenant_id: UUID,
        iep_id: UUID,
        payload: IEPUpdate,
        updated_by: UUID,
    ) -> Optional[IEP]:
        result = await db.execute(
            select(IEP).where(IEP.id == iep_id, IEP.tenant_id == tenant_id)
        )
        iep = result.scalar_one_or_none()
        if not iep:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(iep, field, value)
        iep.updated_by = updated_by

        await db.commit()

        # Re-fetch with relationships
        result = await db.execute(
            select(IEP)
            .where(IEP.id == iep_id)
            .options(*_iep_load_options())
        )
        return result.scalar_one()

    # ------------------------------------------------------------------
    # Delete IEP (hard delete — only DRAFT status allowed)
    # ------------------------------------------------------------------

    @staticmethod
    async def delete_iep(
        db: AsyncSession,
        tenant_id: UUID,
        iep_id: UUID,
    ) -> bool:
        result = await db.execute(
            select(IEP).where(IEP.id == iep_id, IEP.tenant_id == tenant_id)
        )
        iep = result.scalar_one_or_none()
        if not iep:
            return False
        if iep.status != IEPStatus.DRAFT:
            raise ValueError("Only DRAFT IEPs can be deleted. Set status to REVOKED to deactivate.")
        await db.delete(iep)
        await db.commit()
        return True


# ---------------------------------------------------------------------------
# IEP Services (related services: OT, speech, etc.)
# ---------------------------------------------------------------------------

class IEPServiceCRUD:

    @staticmethod
    async def add_service(
        db: AsyncSession,
        tenant_id: UUID,
        iep_id: UUID,
        payload: IEPServiceCreate,
    ) -> IEPService:
        svc = IEPService(tenant_id=tenant_id, iep_id=iep_id, **payload.model_dump())
        db.add(svc)
        await db.commit()
        await db.refresh(svc)
        return svc

    @staticmethod
    async def update_service(
        db: AsyncSession,
        tenant_id: UUID,
        service_id: UUID,
        payload: IEPServiceUpdate,
    ) -> Optional[IEPService]:
        result = await db.execute(
            select(IEPService).where(
                IEPService.id == service_id,
                IEPService.tenant_id == tenant_id,
            )
        )
        svc = result.scalar_one_or_none()
        if not svc:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(svc, field, value)
        await db.commit()
        await db.refresh(svc)
        return svc

    @staticmethod
    async def delete_service(
        db: AsyncSession,
        tenant_id: UUID,
        service_id: UUID,
    ) -> bool:
        result = await db.execute(
            select(IEPService).where(
                IEPService.id == service_id,
                IEPService.tenant_id == tenant_id,
            )
        )
        svc = result.scalar_one_or_none()
        if not svc:
            return False
        await db.delete(svc)
        await db.commit()
        return True


# ---------------------------------------------------------------------------
# IEP Goals
# ---------------------------------------------------------------------------

class IEPGoalCRUD:

    @staticmethod
    async def add_goal(
        db: AsyncSession,
        tenant_id: UUID,
        iep_id: UUID,
        payload: IEPGoalCreate,
    ) -> IEPGoal:
        goal = IEPGoal(tenant_id=tenant_id, iep_id=iep_id, **payload.model_dump())
        db.add(goal)
        await db.commit()
        await db.refresh(goal)
        return goal

    @staticmethod
    async def update_goal(
        db: AsyncSession,
        tenant_id: UUID,
        goal_id: UUID,
        payload: IEPGoalUpdate,
    ) -> Optional[IEPGoal]:
        result = await db.execute(
            select(IEPGoal).where(
                IEPGoal.id == goal_id,
                IEPGoal.tenant_id == tenant_id,
            )
        )
        goal = result.scalar_one_or_none()
        if not goal:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(goal, field, value)
        await db.commit()
        await db.refresh(goal)
        return goal

    @staticmethod
    async def add_progress_note(
        db: AsyncSession,
        tenant_id: UUID,
        goal_id: UUID,
        payload: IEPGoalProgressCreate,
        recorded_by: UUID,
    ) -> IEPGoalProgress:
        note = IEPGoalProgress(
            tenant_id=tenant_id,
            goal_id=goal_id,
            recorded_by=recorded_by,
            **payload.model_dump(),
        )
        db.add(note)
        await db.commit()
        await db.refresh(note)
        return note

    @staticmethod
    async def delete_goal(
        db: AsyncSession,
        tenant_id: UUID,
        goal_id: UUID,
    ) -> bool:
        result = await db.execute(
            select(IEPGoal).where(
                IEPGoal.id == goal_id,
                IEPGoal.tenant_id == tenant_id,
            )
        )
        goal = result.scalar_one_or_none()
        if not goal:
            return False
        await db.delete(goal)
        await db.commit()
        return True


# ---------------------------------------------------------------------------
# IEP Accommodations
# ---------------------------------------------------------------------------

class IEPAccommodationCRUD:

    @staticmethod
    async def add_accommodation(
        db: AsyncSession,
        tenant_id: UUID,
        iep_id: UUID,
        payload: IEPAccommodationCreate,
    ) -> IEPAccommodation:
        acc = IEPAccommodation(tenant_id=tenant_id, iep_id=iep_id, **payload.model_dump())
        db.add(acc)
        await db.commit()
        await db.refresh(acc)
        return acc

    @staticmethod
    async def update_accommodation(
        db: AsyncSession,
        tenant_id: UUID,
        accommodation_id: UUID,
        payload: IEPAccommodationUpdate,
    ) -> Optional[IEPAccommodation]:
        result = await db.execute(
            select(IEPAccommodation).where(
                IEPAccommodation.id == accommodation_id,
                IEPAccommodation.tenant_id == tenant_id,
            )
        )
        acc = result.scalar_one_or_none()
        if not acc:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(acc, field, value)
        await db.commit()
        await db.refresh(acc)
        return acc

    @staticmethod
    async def delete_accommodation(
        db: AsyncSession,
        tenant_id: UUID,
        accommodation_id: UUID,
    ) -> bool:
        result = await db.execute(
            select(IEPAccommodation).where(
                IEPAccommodation.id == accommodation_id,
                IEPAccommodation.tenant_id == tenant_id,
            )
        )
        acc = result.scalar_one_or_none()
        if not acc:
            return False
        await db.delete(acc)
        await db.commit()
        return True


# ---------------------------------------------------------------------------
# IEP Team Members
# ---------------------------------------------------------------------------

class IEPTeamMemberCRUD:

    @staticmethod
    async def add_team_member(
        db: AsyncSession,
        tenant_id: UUID,
        iep_id: UUID,
        payload: IEPTeamMemberCreate,
    ) -> IEPTeamMember:
        member = IEPTeamMember(tenant_id=tenant_id, iep_id=iep_id, **payload.model_dump())
        db.add(member)
        await db.commit()
        await db.refresh(member)
        return member

    @staticmethod
    async def update_team_member(
        db: AsyncSession,
        tenant_id: UUID,
        member_id: UUID,
        payload: IEPTeamMemberUpdate,
    ) -> Optional[IEPTeamMember]:
        result = await db.execute(
            select(IEPTeamMember).where(
                IEPTeamMember.id == member_id,
                IEPTeamMember.tenant_id == tenant_id,
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(member, field, value)
        await db.commit()
        await db.refresh(member)
        return member

    @staticmethod
    async def delete_team_member(
        db: AsyncSession,
        tenant_id: UUID,
        member_id: UUID,
    ) -> bool:
        result = await db.execute(
            select(IEPTeamMember).where(
                IEPTeamMember.id == member_id,
                IEPTeamMember.tenant_id == tenant_id,
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            return False
        await db.delete(member)
        await db.commit()
        return True


# ---------------------------------------------------------------------------
# IEP Meetings
# ---------------------------------------------------------------------------

class IEPMeetingCRUD:

    @staticmethod
    async def add_meeting(
        db: AsyncSession,
        tenant_id: UUID,
        iep_id: UUID,
        payload: IEPMeetingCreate,
        scheduled_by: UUID,
    ) -> IEPMeeting:
        meeting = IEPMeeting(
            tenant_id=tenant_id,
            iep_id=iep_id,
            scheduled_by=scheduled_by,
            **payload.model_dump(),
        )
        db.add(meeting)
        await db.commit()
        await db.refresh(meeting)
        return meeting

    @staticmethod
    async def update_meeting(
        db: AsyncSession,
        tenant_id: UUID,
        meeting_id: UUID,
        payload: IEPMeetingUpdate,
    ) -> Optional[IEPMeeting]:
        result = await db.execute(
            select(IEPMeeting).where(
                IEPMeeting.id == meeting_id,
                IEPMeeting.tenant_id == tenant_id,
            )
        )
        meeting = result.scalar_one_or_none()
        if not meeting:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(meeting, field, value)
        await db.commit()
        await db.refresh(meeting)
        return meeting

    @staticmethod
    async def delete_meeting(
        db: AsyncSession,
        tenant_id: UUID,
        meeting_id: UUID,
    ) -> bool:
        result = await db.execute(
            select(IEPMeeting).where(
                IEPMeeting.id == meeting_id,
                IEPMeeting.tenant_id == tenant_id,
            )
        )
        meeting = result.scalar_one_or_none()
        if not meeting:
            return False
        await db.delete(meeting)
        await db.commit()
        return True


# ---------------------------------------------------------------------------
# Compliance / Deadline Engine
# ---------------------------------------------------------------------------

class IEPComplianceService:
    """
    Scans all active IEPs for upcoming and overdue deadlines.
    Returns IEPDeadlineAlert objects consumed by the API and AI layer (C5).

    Thresholds (IDEA-aligned):
      - critical : deadline <= 14 days away or already past
      - warning  : deadline <= 30 days away
      - info     : deadline <= 60 days away
    """

    CRITICAL_DAYS = 14
    WARNING_DAYS = 30
    INFO_DAYS = 60

    @classmethod
    def _severity(cls, days_remaining: int) -> str:
        if days_remaining <= cls.CRITICAL_DAYS:
            return "critical"
        if days_remaining <= cls.WARNING_DAYS:
            return "warning"
        return "info"

    @classmethod
    async def get_deadline_alerts(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        within_days: int = 60,
    ) -> List[IEPDeadlineAlert]:
        """Return all deadline alerts for active IEPs within `within_days`."""

        today = date.today()

        # Fetch active IEPs with student names
        result = await db.execute(
            select(IEP, Student.first_name, Student.last_name)
            .join(Student, IEP.student_id == Student.id)
            .where(
                IEP.tenant_id == tenant_id,
                IEP.status == IEPStatus.ACTIVE,
            )
        )
        rows = result.all()

        alerts: List[IEPDeadlineAlert] = []

        for iep, first_name, last_name in rows:
            student_name = f"{first_name} {last_name}"

            # Annual review deadline
            review_days = (iep.next_review_date - today).days
            if review_days <= within_days:
                alerts.append(IEPDeadlineAlert(
                    iep_id=iep.id,
                    student_id=iep.student_id,
                    student_name=student_name,
                    alert_type="annual_review",
                    due_date=iep.next_review_date,
                    days_remaining=review_days,
                    severity=cls._severity(review_days),
                ))

            # IEP expiry
            end_days = (iep.end_date - today).days
            if end_days <= within_days:
                alerts.append(IEPDeadlineAlert(
                    iep_id=iep.id,
                    student_id=iep.student_id,
                    student_name=student_name,
                    alert_type="expired" if end_days < 0 else "iep_expiry",
                    due_date=iep.end_date,
                    days_remaining=end_days,
                    severity=cls._severity(end_days),
                ))

            # Triennial re-evaluation
            if iep.triennial_date:
                tri_days = (iep.triennial_date - today).days
                if tri_days <= within_days:
                    alerts.append(IEPDeadlineAlert(
                        iep_id=iep.id,
                        student_id=iep.student_id,
                        student_name=student_name,
                        alert_type="triennial",
                        due_date=iep.triennial_date,
                        days_remaining=tri_days,
                        severity=cls._severity(tri_days),
                    ))

        # Sort: most critical first, then soonest deadline
        alerts.sort(key=lambda a: (
            0 if a.severity == "critical" else 1 if a.severity == "warning" else 2,
            a.days_remaining,
        ))

        return alerts

    @classmethod
    async def get_overdue_ieps(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> List[IEP]:
        """Return active IEPs whose end_date has already passed."""
        today = date.today()
        result = await db.execute(
            select(IEP).where(
                IEP.tenant_id == tenant_id,
                IEP.status == IEPStatus.ACTIVE,
                IEP.end_date < today,
            ).order_by(IEP.end_date.asc())
        )
        return list(result.scalars().all())
