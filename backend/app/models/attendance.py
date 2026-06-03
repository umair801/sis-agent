from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey,
    Index, String, Text, Time, Integer, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship as sa_relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Period(Base):
    __tablename__ = "sis_period"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    school_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_school.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    short_name = Column(String(10), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)

    period_attendances = sa_relationship("AttendancePeriod", back_populates="period")


class AttendanceDaily(Base):
    __tablename__ = "sis_attendance_daily"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_student.id", ondelete="CASCADE"), nullable=False)
    school_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_school.id", ondelete="CASCADE"), nullable=False)
    attendance_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="present")
    excuse_reason = Column(String(255))
    notes = Column(Text)
    recorded_by = Column(PGUUID(as_uuid=True), ForeignKey("sis_user.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "status IN ('present','absent','tardy','excused','half_day')",
            name="sis_attendance_daily_status_check"
        ),
        Index("idx_sis_attendance_daily_student", "student_id", "attendance_date"),
        Index("idx_sis_attendance_daily_school_date", "school_id", "attendance_date"),
    )


class AttendancePeriod(Base):
    __tablename__ = "sis_attendance_period"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_student.id", ondelete="CASCADE"), nullable=False)
    school_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_school.id", ondelete="CASCADE"), nullable=False)
    period_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_period.id", ondelete="CASCADE"), nullable=False)
    attendance_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="present")
    excuse_reason = Column(String(255))
    notes = Column(Text)
    recorded_by = Column(PGUUID(as_uuid=True), ForeignKey("sis_user.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    period = sa_relationship("Period", back_populates="period_attendances")

    __table_args__ = (
        CheckConstraint(
            "status IN ('present','absent','tardy','excused')",
            name="sis_attendance_period_status_check"
        ),
        Index("idx_sis_attendance_period_student", "student_id", "attendance_date"),
        Index("idx_sis_attendance_period_school_date", "school_id", "attendance_date"),
    )