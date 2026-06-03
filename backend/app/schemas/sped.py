"""
Pydantic schemas for SpEd/IEP module.
Covers: IEP, IEPService, IEPGoal, IEPGoalProgress, IEPAccommodation,
        IEPTeamMember, IEPMeeting
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.sped_enums import (
    AccommodationType,
    DisabilityCategory,
    GoalDomain,
    GoalStatus,
    IEPStatus,
    MeetingType,
    ServiceFrequency,
    ServiceType,
    TeamMemberRole,
)


# ===========================================================================
# IEPService
# ===========================================================================

class IEPServiceBase(BaseModel):
    service_type: ServiceType
    provider_name: Optional[str] = None
    minutes_per_session: int = Field(..., gt=0)
    sessions_per_frequency: int = Field(1, gt=0)
    frequency: ServiceFrequency
    start_date: date
    end_date: date
    location: Optional[str] = None
    notes: Optional[str] = None


class IEPServiceCreate(IEPServiceBase):
    pass


class IEPServiceUpdate(BaseModel):
    service_type: Optional[ServiceType] = None
    provider_name: Optional[str] = None
    minutes_per_session: Optional[int] = Field(None, gt=0)
    sessions_per_frequency: Optional[int] = Field(None, gt=0)
    frequency: Optional[ServiceFrequency] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class IEPServiceResponse(IEPServiceBase):
    id: UUID
    iep_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ===========================================================================
# IEPGoalProgress
# ===========================================================================

class IEPGoalProgressBase(BaseModel):
    progress_date: date
    progress_note: str
    mastery_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    status: GoalStatus


class IEPGoalProgressCreate(IEPGoalProgressBase):
    pass


class IEPGoalProgressResponse(IEPGoalProgressBase):
    id: UUID
    goal_id: UUID
    tenant_id: UUID
    recorded_by: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ===========================================================================
# IEPGoal
# ===========================================================================

class IEPGoalBase(BaseModel):
    domain: GoalDomain
    goal_text: str
    baseline: Optional[str] = None
    target_criteria: Optional[str] = None
    measurement_method: Optional[str] = None
    reporting_frequency: Optional[ServiceFrequency] = None
    status: GoalStatus = GoalStatus.NOT_STARTED
    sequence: int = Field(1, ge=1)


class IEPGoalCreate(IEPGoalBase):
    pass


class IEPGoalUpdate(BaseModel):
    domain: Optional[GoalDomain] = None
    goal_text: Optional[str] = None
    baseline: Optional[str] = None
    target_criteria: Optional[str] = None
    measurement_method: Optional[str] = None
    reporting_frequency: Optional[ServiceFrequency] = None
    status: Optional[GoalStatus] = None
    sequence: Optional[int] = Field(None, ge=1)


class IEPGoalResponse(IEPGoalBase):
    id: UUID
    iep_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    progress_notes: List[IEPGoalProgressResponse] = []

    model_config = {"from_attributes": True}


# ===========================================================================
# IEPAccommodation
# ===========================================================================

class IEPAccommodationBase(BaseModel):
    accommodation_type: AccommodationType
    description: str
    applies_to_assessment: bool = False
    applies_to_instruction: bool = True


class IEPAccommodationCreate(IEPAccommodationBase):
    pass


class IEPAccommodationUpdate(BaseModel):
    accommodation_type: Optional[AccommodationType] = None
    description: Optional[str] = None
    applies_to_assessment: Optional[bool] = None
    applies_to_instruction: Optional[bool] = None


class IEPAccommodationResponse(IEPAccommodationBase):
    id: UUID
    iep_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ===========================================================================
# IEPTeamMember
# ===========================================================================

class IEPTeamMemberBase(BaseModel):
    role: TeamMemberRole
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    user_id: Optional[UUID] = None
    signature_obtained: bool = False
    signature_date: Optional[date] = None


class IEPTeamMemberCreate(IEPTeamMemberBase):
    pass


class IEPTeamMemberUpdate(BaseModel):
    role: Optional[TeamMemberRole] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    signature_obtained: Optional[bool] = None
    signature_date: Optional[date] = None


class IEPTeamMemberResponse(IEPTeamMemberBase):
    id: UUID
    iep_id: UUID
    tenant_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ===========================================================================
# IEPMeeting
# ===========================================================================

class IEPMeetingBase(BaseModel):
    meeting_type: MeetingType
    scheduled_date: datetime
    actual_date: Optional[datetime] = None
    location: Optional[str] = None
    attendees: Optional[str] = None
    minutes: Optional[str] = None
    outcome: Optional[str] = None
    next_steps: Optional[str] = None


class IEPMeetingCreate(IEPMeetingBase):
    pass


class IEPMeetingUpdate(BaseModel):
    meeting_type: Optional[MeetingType] = None
    scheduled_date: Optional[datetime] = None
    actual_date: Optional[datetime] = None
    location: Optional[str] = None
    attendees: Optional[str] = None
    minutes: Optional[str] = None
    outcome: Optional[str] = None
    next_steps: Optional[str] = None


class IEPMeetingResponse(IEPMeetingBase):
    id: UUID
    iep_id: UUID
    tenant_id: UUID
    scheduled_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ===========================================================================
# IEP (master record)
# ===========================================================================

class IEPBase(BaseModel):
    disability_category: DisabilityCategory
    secondary_disability: Optional[DisabilityCategory] = None
    iep_number: Optional[str] = None
    eligibility_date: date
    start_date: date
    end_date: date
    next_review_date: date
    triennial_date: Optional[date] = None
    least_restrictive_environment: Optional[str] = None
    placement_percentage_general_ed: Optional[Decimal] = Field(None, ge=0, le=100)
    present_levels: Optional[str] = None
    transition_plan: Optional[str] = None
    extended_school_year: bool = False
    notes: Optional[str] = None


class IEPCreate(IEPBase):
    student_id: UUID
    status: IEPStatus = IEPStatus.DRAFT
    # Nested creation — all optional at creation time
    services: List[IEPServiceCreate] = []
    goals: List[IEPGoalCreate] = []
    accommodations: List[IEPAccommodationCreate] = []
    team_members: List[IEPTeamMemberCreate] = []


class IEPUpdate(BaseModel):
    disability_category: Optional[DisabilityCategory] = None
    secondary_disability: Optional[DisabilityCategory] = None
    iep_number: Optional[str] = None
    status: Optional[IEPStatus] = None
    eligibility_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    next_review_date: Optional[date] = None
    triennial_date: Optional[date] = None
    least_restrictive_environment: Optional[str] = None
    placement_percentage_general_ed: Optional[Decimal] = Field(None, ge=0, le=100)
    present_levels: Optional[str] = None
    transition_plan: Optional[str] = None
    extended_school_year: Optional[bool] = None
    notes: Optional[str] = None


class IEPResponse(IEPBase):
    id: UUID
    tenant_id: UUID
    student_id: UUID
    status: IEPStatus
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    # Nested collections
    services: List[IEPServiceResponse] = []
    goals: List[IEPGoalResponse] = []
    accommodations: List[IEPAccommodationResponse] = []
    team_members: List[IEPTeamMemberResponse] = []
    meetings: List[IEPMeetingResponse] = []

    model_config = {"from_attributes": True}


class IEPSummary(BaseModel):
    """Lightweight response for list endpoints — no nested collections."""
    id: UUID
    student_id: UUID
    tenant_id: UUID
    iep_number: Optional[str] = None
    status: IEPStatus
    disability_category: DisabilityCategory
    start_date: date
    end_date: date
    next_review_date: date
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ===========================================================================
# Compliance / deadline alert schema (used by AI layer in C5)
# ===========================================================================

class IEPDeadlineAlert(BaseModel):
    iep_id: UUID
    student_id: UUID
    student_name: str
    alert_type: str          # "annual_review", "triennial", "expired"
    due_date: date
    days_remaining: int
    severity: str            # "critical", "warning", "info"
