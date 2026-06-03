from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


# ------------------------------------------------------------------ #
# Course
# ------------------------------------------------------------------ #

class CourseBase(BaseModel):
    course_code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    credits: Decimal = Field(default=Decimal("1.0"), ge=0)
    grade_level_min: Optional[int] = None
    grade_level_max: Optional[int] = None
    department: Optional[str] = Field(None, max_length=100)
    is_active: bool = True


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    credits: Optional[Decimal] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None


class CourseResponse(CourseBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ------------------------------------------------------------------ #
# Room
# ------------------------------------------------------------------ #

class RoomBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    room_number: Optional[str] = Field(None, max_length=20)
    capacity: int = Field(default=30, ge=1)
    room_type: str = Field(default="classroom", max_length=50)
    is_active: bool = True


class RoomCreate(RoomBase):
    school_id: UUID


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    room_type: Optional[str] = None
    is_active: Optional[bool] = None


class RoomResponse(RoomBase):
    id: UUID
    tenant_id: UUID
    school_id: UUID

    model_config = {"from_attributes": True}


# ------------------------------------------------------------------ #
# Section
# ------------------------------------------------------------------ #

class SectionCreate(BaseModel):
    school_id: UUID
    course_id: UUID
    academic_year_id: UUID
    period_id: UUID
    room_id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None
    section_number: str = Field(default="01", max_length=10)
    max_enrollment: int = Field(default=30, ge=1)


class SectionUpdate(BaseModel):
    period_id: Optional[UUID] = None
    room_id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None
    max_enrollment: Optional[int] = None
    is_active: Optional[bool] = None


class SectionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    school_id: UUID
    course_id: UUID
    academic_year_id: UUID
    period_id: UUID
    room_id: Optional[UUID]
    teacher_id: Optional[UUID]
    section_number: str
    max_enrollment: int
    current_enrollment: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SectionDetailResponse(SectionResponse):
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    period_name: Optional[str] = None
    room_name: Optional[str] = None
    teacher_name: Optional[str] = None


# ------------------------------------------------------------------ #
# Student section enrollment
# ------------------------------------------------------------------ #

class StudentSectionCreate(BaseModel):
    student_id: UUID
    section_id: UUID
    enrolled_date: Optional[date] = None


class StudentSectionDrop(BaseModel):
    dropped_date: date
    reason: Optional[str] = None


class StudentSectionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    student_id: UUID
    section_id: UUID
    enrolled_date: date
    dropped_date: Optional[date]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ------------------------------------------------------------------ #
# Conflict detection
# ------------------------------------------------------------------ #

class ConflictType(str):
    TEACHER_DOUBLE_BOOKED = "teacher_double_booked"
    ROOM_DOUBLE_BOOKED = "room_double_booked"
    STUDENT_DOUBLE_BOOKED = "student_double_booked"
    ROOM_OVER_CAPACITY = "room_over_capacity"


class ScheduleConflict(BaseModel):
    conflict_type: str
    severity: str
    description: str
    section_id_1: Optional[UUID] = None
    section_id_2: Optional[UUID] = None
    affected_entity_id: Optional[UUID] = None
    affected_entity_name: Optional[str] = None
    period_name: Optional[str] = None
    suggestion: Optional[str] = None


class ConflictCheckResult(BaseModel):
    has_conflicts: bool
    conflict_count: int
    conflicts: List[ScheduleConflict]