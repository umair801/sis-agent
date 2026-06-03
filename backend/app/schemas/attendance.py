from datetime import date, datetime, time
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


# ------------------------------------------------------------------ #
# Period schemas
# ------------------------------------------------------------------ #

class PeriodResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    school_id: UUID
    name: str
    short_name: str
    start_time: time
    end_time: time
    sort_order: int
    is_active: bool

    model_config = {"from_attributes": True}


# ------------------------------------------------------------------ #
# Daily attendance schemas
# ------------------------------------------------------------------ #

class AttendanceDailyCreate(BaseModel):
    student_id: UUID
    school_id: UUID
    attendance_date: date
    status: str = Field(default="present")
    excuse_reason: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None

    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"present", "absent", "tardy", "excused", "half_day"}
        if v not in allowed:
            raise ValueError(f"Status must be one of: {allowed}")
        return v


class AttendanceDailyUpdate(BaseModel):
    status: Optional[str] = None
    excuse_reason: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class AttendanceDailyResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    student_id: UUID
    school_id: UUID
    attendance_date: date
    status: str
    excuse_reason: Optional[str]
    notes: Optional[str]
    recorded_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ------------------------------------------------------------------ #
# Bulk daily attendance (teacher submits whole class at once)
# ------------------------------------------------------------------ #

class BulkAttendanceEntry(BaseModel):
    student_id: UUID
    status: str = "present"
    excuse_reason: Optional[str] = None
    notes: Optional[str] = None


class BulkAttendanceDailyCreate(BaseModel):
    school_id: UUID
    attendance_date: date
    entries: List[BulkAttendanceEntry] = Field(..., min_length=1)


class BulkAttendanceResult(BaseModel):
    created: int
    updated: int
    total: int


# ------------------------------------------------------------------ #
# Period attendance schemas
# ------------------------------------------------------------------ #

class AttendancePeriodCreate(BaseModel):
    student_id: UUID
    school_id: UUID
    period_id: UUID
    attendance_date: date
    status: str = Field(default="present")
    excuse_reason: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class AttendancePeriodUpdate(BaseModel):
    status: Optional[str] = None
    excuse_reason: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class AttendancePeriodResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    student_id: UUID
    school_id: UUID
    period_id: UUID
    attendance_date: date
    status: str
    excuse_reason: Optional[str]
    notes: Optional[str]
    recorded_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BulkPeriodAttendanceEntry(BaseModel):
    student_id: UUID
    period_id: UUID
    status: str = "present"
    excuse_reason: Optional[str] = None
    notes: Optional[str] = None


class BulkAttendancePeriodCreate(BaseModel):
    school_id: UUID
    attendance_date: date
    entries: List[BulkPeriodAttendanceEntry] = Field(..., min_length=1)


# ------------------------------------------------------------------ #
# Reporting schemas
# ------------------------------------------------------------------ #

class AttendanceReportParams(BaseModel):
    school_id: Optional[UUID] = None
    student_id: Optional[UUID] = None
    date_from: date
    date_to: date
    status: Optional[str] = None


class StudentAttendanceSummary(BaseModel):
    student_id: UUID
    student_number: str
    first_name: str
    last_name: str
    total_days: int
    present: int
    absent: int
    tardy: int
    excused: int
    half_day: int
    attendance_rate: float


class DailyAttendanceSummary(BaseModel):
    attendance_date: date
    school_id: UUID
    total_students: int
    present: int
    absent: int
    tardy: int
    excused: int
    half_day: int
    attendance_rate: float