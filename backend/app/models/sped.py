"""
SpEd/IEP models for AgAI_30 SIS.
Covers: IEP records, services, goals, accommodations, team members, meeting logs.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Column, String, Text, Boolean, Date, DateTime,
    ForeignKey, Numeric, Integer, UniqueConstraint, Index
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship as sa_relationship
from sqlalchemy.sql import func

from app.db.database import Base
from app.models.sped_enums import (
    IEPStatus, DisabilityCategory, ServiceType, ServiceFrequency,
    GoalStatus, GoalDomain, AccommodationType, TeamMemberRole, MeetingType,
)


# ---------------------------------------------------------------------------
# sis_iep  (master IEP record)
# ---------------------------------------------------------------------------

class IEP(Base):
    __tablename__ = "sis_iep"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("sis_student.id", ondelete="CASCADE"), nullable=False)

    # Identity / dates
    iep_number = Column(String(50), nullable=True)          # district-assigned reference
    status = Column(SAEnum(IEPStatus), nullable=False, default=IEPStatus.DRAFT)
    disability_category = Column(SAEnum(DisabilityCategory), nullable=False)
    secondary_disability = Column(SAEnum(DisabilityCategory), nullable=True)

    # Timeline (IDEA compliance requires exact dates)
    eligibility_date = Column(Date, nullable=False)         # date student was found eligible
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)                 # must be reviewed before this date
    next_review_date = Column(Date, nullable=False)         # annual review deadline
    triennial_date = Column(Date, nullable=True)            # re-evaluation deadline (every 3 yrs)

    # Placement
    least_restrictive_environment = Column(Text, nullable=True)
    placement_percentage_general_ed = Column(Numeric(5, 2), nullable=True)  # e.g. 80.00

    # Narrative sections (stored as text; AI can generate drafts)
    present_levels = Column(Text, nullable=True)
    transition_plan = Column(Text, nullable=True)
    extended_school_year = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)

    # Audit
    created_by = Column(UUID(as_uuid=True), ForeignKey("sis_user.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("sis_user.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    tenant = sa_relationship("Tenant", foreign_keys=[tenant_id])
    student = sa_relationship("Student", foreign_keys=[student_id])
    services = sa_relationship("IEPService", back_populates="iep", cascade="all, delete-orphan")
    goals = sa_relationship("IEPGoal", back_populates="iep", cascade="all, delete-orphan")
    accommodations = sa_relationship("IEPAccommodation", back_populates="iep", cascade="all, delete-orphan")
    team_members = sa_relationship("IEPTeamMember", back_populates="iep", cascade="all, delete-orphan")
    meetings = sa_relationship("IEPMeeting", back_populates="iep", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sis_iep_tenant_student", "tenant_id", "student_id"),
        Index("ix_sis_iep_status", "status"),
        Index("ix_sis_iep_next_review", "next_review_date"),
    )

    def __repr__(self):
        return f"<IEP id={self.id} student={self.student_id} status={self.status}>"


# ---------------------------------------------------------------------------
# sis_iep_service  (related services: hours, frequency, provider)
# ---------------------------------------------------------------------------

class IEPService(Base):
    __tablename__ = "sis_iep_service"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    iep_id = Column(UUID(as_uuid=True), ForeignKey("sis_iep.id", ondelete="CASCADE"), nullable=False)

    service_type = Column(SAEnum(ServiceType), nullable=False)
    provider_name = Column(String(200), nullable=True)
    minutes_per_session = Column(Integer, nullable=False)
    sessions_per_frequency = Column(Integer, nullable=False, default=1)
    frequency = Column(SAEnum(ServiceFrequency), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    location = Column(String(200), nullable=True)           # e.g. "Resource Room", "General Ed"
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    iep = sa_relationship("IEP", back_populates="services")

    __table_args__ = (
        Index("ix_sis_iep_service_iep", "iep_id"),
    )


# ---------------------------------------------------------------------------
# sis_iep_goal
# ---------------------------------------------------------------------------

class IEPGoal(Base):
    __tablename__ = "sis_iep_goal"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    iep_id = Column(UUID(as_uuid=True), ForeignKey("sis_iep.id", ondelete="CASCADE"), nullable=False)

    domain = Column(SAEnum(GoalDomain), nullable=False)
    goal_text = Column(Text, nullable=False)
    baseline = Column(Text, nullable=True)
    target_criteria = Column(Text, nullable=True)           # measurable outcome
    measurement_method = Column(Text, nullable=True)
    reporting_frequency = Column(SAEnum(ServiceFrequency), nullable=True)
    status = Column(SAEnum(GoalStatus), nullable=False, default=GoalStatus.NOT_STARTED)
    sequence = Column(Integer, nullable=False, default=1)   # display order

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    iep = sa_relationship("IEP", back_populates="goals")
    progress_notes = sa_relationship("IEPGoalProgress", back_populates="goal", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sis_iep_goal_iep", "iep_id"),
    )


# ---------------------------------------------------------------------------
# sis_iep_goal_progress  (progress monitoring notes per goal)
# ---------------------------------------------------------------------------

class IEPGoalProgress(Base):
    __tablename__ = "sis_iep_goal_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("sis_iep_goal.id", ondelete="CASCADE"), nullable=False)
    recorded_by = Column(UUID(as_uuid=True), ForeignKey("sis_user.id"), nullable=True)

    progress_date = Column(Date, nullable=False)
    progress_note = Column(Text, nullable=False)
    mastery_percentage = Column(Numeric(5, 2), nullable=True)
    status = Column(SAEnum(GoalStatus), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    goal = sa_relationship("IEPGoal", back_populates="progress_notes")

    __table_args__ = (
        Index("ix_sis_iep_goal_progress_goal", "goal_id"),
    )


# ---------------------------------------------------------------------------
# sis_iep_accommodation
# ---------------------------------------------------------------------------

class IEPAccommodation(Base):
    __tablename__ = "sis_iep_accommodation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    iep_id = Column(UUID(as_uuid=True), ForeignKey("sis_iep.id", ondelete="CASCADE"), nullable=False)

    accommodation_type = Column(SAEnum(AccommodationType), nullable=False)
    description = Column(Text, nullable=False)
    applies_to_assessment = Column(Boolean, nullable=False, default=False)
    applies_to_instruction = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    iep = sa_relationship("IEP", back_populates="accommodations")

    __table_args__ = (
        Index("ix_sis_iep_accommodation_iep", "iep_id"),
    )


# ---------------------------------------------------------------------------
# sis_iep_team_member
# ---------------------------------------------------------------------------

class IEPTeamMember(Base):
    __tablename__ = "sis_iep_team_member"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    iep_id = Column(UUID(as_uuid=True), ForeignKey("sis_iep.id", ondelete="CASCADE"), nullable=False)

    role = Column(SAEnum(TeamMemberRole), nullable=False)
    name = Column(String(200), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("sis_user.id"), nullable=True)  # linked SIS user if exists
    signature_obtained = Column(Boolean, nullable=False, default=False)
    signature_date = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    iep = sa_relationship("IEP", back_populates="team_members")

    __table_args__ = (
        UniqueConstraint("iep_id", "user_id", name="uq_sis_iep_team_user"),
        Index("ix_sis_iep_team_iep", "iep_id"),
    )


# ---------------------------------------------------------------------------
# sis_iep_meeting
# ---------------------------------------------------------------------------

class IEPMeeting(Base):
    __tablename__ = "sis_iep_meeting"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    iep_id = Column(UUID(as_uuid=True), ForeignKey("sis_iep.id", ondelete="CASCADE"), nullable=False)
    scheduled_by = Column(UUID(as_uuid=True), ForeignKey("sis_user.id"), nullable=True)

    meeting_type = Column(SAEnum(MeetingType), nullable=False)
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    actual_date = Column(DateTime(timezone=True), nullable=True)
    location = Column(String(200), nullable=True)
    attendees = Column(Text, nullable=True)                 # comma-separated names / JSON summary
    minutes = Column(Text, nullable=True)
    outcome = Column(Text, nullable=True)
    next_steps = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    iep = sa_relationship("IEP", back_populates="meetings")

    __table_args__ = (
        Index("ix_sis_iep_meeting_iep", "iep_id"),
        Index("ix_sis_iep_meeting_date", "scheduled_date"),
    )