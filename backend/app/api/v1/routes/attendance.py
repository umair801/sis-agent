from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_roles
from app.db.database import get_db
from app.schemas.attendance import (
    AttendanceDailyCreate, AttendanceDailyUpdate, AttendanceDailyResponse,
    BulkAttendanceDailyCreate, BulkAttendanceResult,
    AttendancePeriodCreate, AttendancePeriodUpdate, AttendancePeriodResponse,
    BulkAttendancePeriodCreate,
    AttendanceReportParams, StudentAttendanceSummary, DailyAttendanceSummary,
    PeriodResponse
)
from app.services.attendance_service import AttendanceService
from app.schemas.auth import TokenPayload

router = APIRouter(prefix="/attendance", tags=["Attendance"])

RECORD_ROLES = ["SuperAdmin", "DistrictAdmin", "Principal", "Teacher"]
READ_ROLES = ["SuperAdmin", "DistrictAdmin", "Principal", "Teacher", "SpEdCoordinator"]
REPORT_ROLES = ["SuperAdmin", "DistrictAdmin", "Principal"]


# ------------------------------------------------------------------ #
# Periods lookup
# ------------------------------------------------------------------ #

@router.get("/periods", response_model=list[PeriodResponse])
async def get_periods(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*READ_ROLES))
):
    return await AttendanceService.get_periods(db, UUID(current_user.tenant_id), school_id)


# ------------------------------------------------------------------ #
# Daily attendance
# ------------------------------------------------------------------ #

@router.post("/daily", response_model=AttendanceDailyResponse, status_code=status.HTTP_201_CREATED)
async def record_daily(
    payload: AttendanceDailyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*RECORD_ROLES))
):
    record, _ = await AttendanceService.upsert_daily(
        db, UUID(current_user.tenant_id), UUID(current_user.sub), payload
    )
    return record


@router.post("/daily/bulk", response_model=BulkAttendanceResult)
async def bulk_record_daily(
    payload: BulkAttendanceDailyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*RECORD_ROLES))
):
    return await AttendanceService.bulk_upsert_daily(
        db, UUID(current_user.tenant_id), UUID(current_user.sub), payload
    )


@router.get("/daily", response_model=list[AttendanceDailyResponse])
async def get_daily_by_date(
    school_id: UUID = Query(...),
    attendance_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*READ_ROLES))
):
    return await AttendanceService.get_daily_by_date(
        db, UUID(current_user.tenant_id), school_id, attendance_date
    )


@router.get("/daily/student/{student_id}", response_model=list[AttendanceDailyResponse])
async def get_student_daily(
    student_id: UUID,
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*READ_ROLES))
):
    return await AttendanceService.get_student_daily(
        db, UUID(current_user.tenant_id), student_id, date_from, date_to
    )


@router.patch("/daily/{record_id}", response_model=AttendanceDailyResponse)
async def update_daily(
    record_id: UUID,
    payload: AttendanceDailyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*RECORD_ROLES))
):
    record = await AttendanceService.update_daily(
        db, UUID(current_user.tenant_id), record_id, payload
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")
    return record


# ------------------------------------------------------------------ #
# Period attendance
# ------------------------------------------------------------------ #

@router.post("/period", response_model=AttendancePeriodResponse, status_code=status.HTTP_201_CREATED)
async def record_period(
    payload: AttendancePeriodCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*RECORD_ROLES))
):
    record, _ = await AttendanceService.upsert_period(
        db, UUID(current_user.tenant_id), UUID(current_user.sub), payload
    )
    return record


@router.post("/period/bulk", response_model=BulkAttendanceResult)
async def bulk_record_period(
    payload: BulkAttendancePeriodCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*RECORD_ROLES))
):
    return await AttendanceService.bulk_upsert_period(
        db, UUID(current_user.tenant_id), UUID(current_user.sub), payload
    )


@router.get("/period", response_model=list[AttendancePeriodResponse])
async def get_period_attendance(
    school_id: UUID = Query(...),
    attendance_date: date = Query(...),
    period_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*READ_ROLES))
):
    return await AttendanceService.get_period_attendance_by_date(
        db, UUID(current_user.tenant_id), school_id, attendance_date, period_id
    )


# ------------------------------------------------------------------ #
# Reports
# ------------------------------------------------------------------ #

@router.get("/reports/student-summary", response_model=list[StudentAttendanceSummary])
async def student_attendance_summary(
    date_from: date = Query(...),
    date_to: date = Query(...),
    school_id: Optional[UUID] = Query(None),
    student_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*REPORT_ROLES))
):
    params = AttendanceReportParams(
        school_id=school_id,
        student_id=student_id,
        date_from=date_from,
        date_to=date_to,
        status=status_filter
    )
    return await AttendanceService.get_student_summary(db, UUID(current_user.tenant_id), params)


@router.get("/reports/daily-summary", response_model=list[DailyAttendanceSummary])
async def daily_attendance_summary(
    school_id: UUID = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*REPORT_ROLES))
):
    return await AttendanceService.get_daily_summary(
        db, UUID(current_user.tenant_id), school_id, date_from, date_to
    )