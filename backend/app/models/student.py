from datetime import date, datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey,
    Index, String, Text, Integer, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship as sa_relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Student(Base):
    __tablename__ = "sis_student"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    student_number = Column(String(50), nullable=False)
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(20))
    ethnicity = Column(String(50))
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    phone = Column(String(30))
    email = Column(String(255))
    photo_url = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    guardians = sa_relationship("Guardian", back_populates="student", cascade="all, delete-orphan")
    enrollments = sa_relationship("Enrollment", back_populates="student")

    __table_args__ = (
        Index("idx_sis_student_tenant", "tenant_id"),
        Index("idx_sis_student_name", "tenant_id", "last_name", "first_name"),
    )


class Guardian(Base):
    __tablename__ = "sis_guardian"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_student.id", ondelete="CASCADE"), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    relationship = Column(String(50), nullable=False)
    phone_primary = Column(String(30))
    phone_secondary = Column(String(30))
    email = Column(String(255))
    is_emergency_contact = Column(Boolean, nullable=False, default=False)
    is_authorized_pickup = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    student = sa_relationship("Student", back_populates="guardians")


class School(Base):
    __tablename__ = "sis_school"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    short_name = Column(String(50))
    address = Column(String(255))
    phone = Column(String(30))
    principal_name = Column(String(150))
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    enrollments = sa_relationship("Enrollment", back_populates="school")


class AcademicYear(Base):
    __tablename__ = "sis_academic_year"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_current = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    enrollments = sa_relationship("Enrollment", back_populates="academic_year")


class GradeLevel(Base):
    __tablename__ = "sis_grade_level"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    short_name = Column(String(10), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)

    enrollments = sa_relationship("Enrollment", back_populates="grade_level")


class Enrollment(Base):
    __tablename__ = "sis_enrollment"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_student.id", ondelete="CASCADE"), nullable=False)
    school_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_school.id", ondelete="RESTRICT"), nullable=False)
    academic_year_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_academic_year.id", ondelete="RESTRICT"), nullable=False)
    grade_level_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_grade_level.id", ondelete="RESTRICT"), nullable=False)
    enrollment_date = Column(Date, nullable=False)
    withdrawal_date = Column(Date)
    withdrawal_reason = Column(String(255))
    status = Column(String(30), nullable=False, default="active")
    homeroom_teacher_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_user.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    student = sa_relationship("Student", back_populates="enrollments")
    school = sa_relationship("School", back_populates="enrollments")
    academic_year = sa_relationship("AcademicYear", back_populates="enrollments")
    grade_level = sa_relationship("GradeLevel", back_populates="enrollments")

    __table_args__ = (
        CheckConstraint(
            "status IN ('active','withdrawn','graduated','transferred','suspended')",
            name="sis_enrollment_status_check"
        ),
        Index("idx_sis_enrollment_student", "student_id"),
        Index("idx_sis_enrollment_tenant_year", "tenant_id", "academic_year_id"),
    )