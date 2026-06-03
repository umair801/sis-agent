from datetime import date
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceDaily, AttendancePeriod, Period
from app.models.student import Student
from app.schemas.attendance import (
    AttendanceDailyCreate, AttendanceDailyUpdate,
    BulkAttendanceDailyCreate, BulkAttendanceResult,
    AttendancePeriodCreate, AttendancePeriodUpdate,
    BulkAttendancePeriodCreate,
    AttendanceReportParams, StudentAttendanceSummary, DailyAttendanceSummary
)
from app.core.logging import logger


class AttendanceService:

    # ---------------------------------------------------------- #
    # Periods
    # ---------------------------------------------------------- #

    @staticmethod
    async def get_periods(
        db: AsyncSession,
        tenant_id: UUID,
        school_id: UUID
    ) -> List[Period]:
        result = await db.execute(
            select(Period).where(
                Period.tenant_id == tenant_id,
                Period.school_id == school_id,
                Period.is_active == True
            ).order_by(Period.sort_order)
        )
        return result.scalars().all()

    # ---------------------------------------------------------- #
    # Daily attendance
    # ---------------------------------------------------------- #

    @staticmethod
    async def upsert_daily(
        db: AsyncSession,
        tenant_id: UUID,
        recorded_by: UUID,
        payload: AttendanceDailyCreate
    ) -> Tuple[AttendanceDaily, bool]:
        result = await db.execute(
            select(AttendanceDaily).where(
                AttendanceDaily.tenant_id == tenant_id,
                AttendanceDaily.student_id == payload.student_id,
                AttendanceDaily.attendance_date == payload.attendance_date
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.status = payload.status
            existing.excuse_reason = payload.excuse_reason
            existing.notes = payload.notes
            existing.recorded_by = recorded_by
            await db.commit()
            await db.refresh(existing)
            return existing, False
        else:
            record = AttendanceDaily(
                tenant_id=tenant_id,
                recorded_by=recorded_by,
                **payload.model_dump()
            )
            db.add(record)
            await db.commit()
            await db.refresh(record)
            return record, True

    @staticmethod
    async def bulk_upsert_daily(
        db: AsyncSession,
        tenant_id: UUID,
        recorded_by: UUID,
        payload: BulkAttendanceDailyCreate
    ) -> BulkAttendanceResult:
        created = 0
        updated = 0

        for entry in payload.entries:
            single = AttendanceDailyCreate(
                student_id=entry.student_id,
                school_id=payload.school_id,
                attendance_date=payload.attendance_date,
                status=entry.status,
                excuse_reason=entry.excuse_reason,
                notes=entry.notes
            )
            _, is_new = await AttendanceService.upsert_daily(db, tenant_id, recorded_by, single)
            if is_new:
                created += 1
            else:
                updated += 1

        logger.info(
            f"Bulk daily attendance: {created} created, {updated} updated "
            f"for date {payload.attendance_date} by {recorded_by}"
        )
        return BulkAttendanceResult(created=created, updated=updated, total=created + updated)

    @staticmethod
    async def get_daily_by_date(
        db: AsyncSession,
        tenant_id: UUID,
        school_id: UUID,
        attendance_date: date
    ) -> List[AttendanceDaily]:
        result = await db.execute(
            select(AttendanceDaily).where(
                AttendanceDaily.tenant_id == tenant_id,
                AttendanceDaily.school_id == school_id,
                AttendanceDaily.attendance_date == attendance_date
            ).order_by(AttendanceDaily.student_id)
        )
        return result.scalars().all()

    @staticmethod
    async def get_student_daily(
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID,
        date_from: date,
        date_to: date
    ) -> List[AttendanceDaily]:
        result = await db.execute(
            select(AttendanceDaily).where(
                AttendanceDaily.tenant_id == tenant_id,
                AttendanceDaily.student_id == student_id,
                AttendanceDaily.attendance_date >= date_from,
                AttendanceDaily.attendance_date <= date_to
            ).order_by(AttendanceDaily.attendance_date)
        )
        return result.scalars().all()

    @staticmethod
    async def update_daily(
        db: AsyncSession,
        tenant_id: UUID,
        record_id: UUID,
        payload: AttendanceDailyUpdate
    ) -> Optional[AttendanceDaily]:
        result = await db.execute(
            select(AttendanceDaily).where(
                AttendanceDaily.id == record_id,
                AttendanceDaily.tenant_id == tenant_id
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            return None
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(record, field, value)
        await db.commit()
        await db.refresh(record)
        return record

    # ---------------------------------------------------------- #
    # Period attendance
    # ---------------------------------------------------------- #

    @staticmethod
    async def upsert_period(
        db: AsyncSession,
        tenant_id: UUID,
        recorded_by: UUID,
        payload: AttendancePeriodCreate
    ) -> Tuple[AttendancePeriod, bool]:
        result = await db.execute(
            select(AttendancePeriod).where(
                AttendancePeriod.tenant_id == tenant_id,
                AttendancePeriod.student_id == payload.student_id,
                AttendancePeriod.period_id == payload.period_id,
                AttendancePeriod.attendance_date == payload.attendance_date
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.status = payload.status
            existing.excuse_reason = payload.excuse_reason
            existing.notes = payload.notes
            existing.recorded_by = recorded_by
            await db.commit()
            await db.refresh(existing)
            return existing, False
        else:
            record = AttendancePeriod(
                tenant_id=tenant_id,
                recorded_by=recorded_by,
                **payload.model_dump()
            )
            db.add(record)
            await db.commit()
            await db.refresh(record)
            return record, True

    @staticmethod
    async def bulk_upsert_period(
        db: AsyncSession,
        tenant_id: UUID,
        recorded_by: UUID,
        payload: BulkAttendancePeriodCreate
    ) -> BulkAttendanceResult:
        created = 0
        updated = 0

        for entry in payload.entries:
            single = AttendancePeriodCreate(
                student_id=entry.student_id,
                school_id=payload.school_id,
                period_id=entry.period_id,
                attendance_date=payload.attendance_date,
                status=entry.status,
                excuse_reason=entry.excuse_reason,
                notes=entry.notes
            )
            _, is_new = await AttendanceService.upsert_period(db, tenant_id, recorded_by, single)
            if is_new:
                created += 1
            else:
                updated += 1

        return BulkAttendanceResult(created=created, updated=updated, total=created + updated)

    @staticmethod
    async def get_period_attendance_by_date(
        db: AsyncSession,
        tenant_id: UUID,
        school_id: UUID,
        attendance_date: date,
        period_id: Optional[UUID] = None
    ) -> List[AttendancePeriod]:
        query = select(AttendancePeriod).where(
            AttendancePeriod.tenant_id == tenant_id,
            AttendancePeriod.school_id == school_id,
            AttendancePeriod.attendance_date == attendance_date
        )
        if period_id:
            query = query.where(AttendancePeriod.period_id == period_id)
        result = await db.execute(query.order_by(AttendancePeriod.period_id, AttendancePeriod.student_id))
        return result.scalars().all()

    # ---------------------------------------------------------- #
    # Reporting
    # ---------------------------------------------------------- #

    @staticmethod
    async def get_student_summary(
        db: AsyncSession,
        tenant_id: UUID,
        params: AttendanceReportParams
    ) -> List[StudentAttendanceSummary]:
        query = (
            select(
                Student.id.label("student_id"),
                Student.student_number,
                Student.first_name,
                Student.last_name,
                func.count(AttendanceDaily.id).label("total_days"),
                func.sum(case((AttendanceDaily.status == "present", 1), else_=0)).label("present"),
                func.sum(case((AttendanceDaily.status == "absent", 1), else_=0)).label("absent"),
                func.sum(case((AttendanceDaily.status == "tardy", 1), else_=0)).label("tardy"),
                func.sum(case((AttendanceDaily.status == "excused", 1), else_=0)).label("excused"),
                func.sum(case((AttendanceDaily.status == "half_day", 1), else_=0)).label("half_day"),
            )
            .join(AttendanceDaily, and_(
                AttendanceDaily.student_id == Student.id,
                AttendanceDaily.tenant_id == tenant_id,
                AttendanceDaily.attendance_date >= params.date_from,
                AttendanceDaily.attendance_date <= params.date_to
            ))
            .where(Student.tenant_id == tenant_id, Student.is_deleted == False)
            .group_by(Student.id, Student.student_number, Student.first_name, Student.last_name)
        )

        if params.student_id:
            query = query.where(Student.id == params.student_id)
        if params.school_id:
            query = query.where(AttendanceDaily.school_id == params.school_id)
        if params.status:
            query = query.having(
                func.sum(case((AttendanceDaily.status == params.status, 1), else_=0)) > 0
            )

        result = await db.execute(query.order_by(Student.last_name, Student.first_name))
        rows = result.all()

        summaries = []
        for row in rows:
            total = row.total_days or 1
            rate = round((row.present / total) * 100, 1)
            summaries.append(StudentAttendanceSummary(
                student_id=row.student_id,
                student_number=row.student_number,
                first_name=row.first_name,
                last_name=row.last_name,
                total_days=row.total_days,
                present=row.present,
                absent=row.absent,
                tardy=row.tardy,
                excused=row.excused,
                half_day=row.half_day,
                attendance_rate=rate
            ))
        return summaries

    @staticmethod
    async def get_daily_summary(
        db: AsyncSession,
        tenant_id: UUID,
        school_id: UUID,
        date_from: date,
        date_to: date
    ) -> List[DailyAttendanceSummary]:
        query = (
            select(
                AttendanceDaily.attendance_date,
                AttendanceDaily.school_id,
                func.count(AttendanceDaily.id).label("total_students"),
                func.sum(case((AttendanceDaily.status == "present", 1), else_=0)).label("present"),
                func.sum(case((AttendanceDaily.status == "absent", 1), else_=0)).label("absent"),
                func.sum(case((AttendanceDaily.status == "tardy", 1), else_=0)).label("tardy"),
                func.sum(case((AttendanceDaily.status == "excused", 1), else_=0)).label("excused"),
                func.sum(case((AttendanceDaily.status == "half_day", 1), else_=0)).label("half_day"),
            )
            .where(
                AttendanceDaily.tenant_id == tenant_id,
                AttendanceDaily.school_id == school_id,
                AttendanceDaily.attendance_date >= date_from,
                AttendanceDaily.attendance_date <= date_to
            )
            .group_by(AttendanceDaily.attendance_date, AttendanceDaily.school_id)
            .order_by(AttendanceDaily.attendance_date)
        )
        result = await db.execute(query)
        rows = result.all()

        summaries = []
        for row in rows:
            total = row.total_students or 1
            rate = round((row.present / total) * 100, 1)
            summaries.append(DailyAttendanceSummary(
                attendance_date=row.attendance_date,
                school_id=row.school_id,
                total_students=row.total_students,
                present=row.present,
                absent=row.absent,
                tardy=row.tardy,
                excused=row.excused,
                half_day=row.half_day,
                attendance_rate=rate
            ))
        return summaries