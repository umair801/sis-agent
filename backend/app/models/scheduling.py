from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey,
    Index, Integer, Numeric, String, Text, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship as sa_relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Course(Base):
    __tablename__ = "sis_course"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    course_code = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    credits = Column(Numeric(4, 2), nullable=False, default=1.0)
    grade_level_min = Column(Integer)
    grade_level_max = Column(Integer)
    department = Column(String(100))
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    sections = sa_relationship("Section", back_populates="course")


class Room(Base):
    __tablename__ = "sis_room"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    school_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_school.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    room_number = Column(String(20))
    capacity = Column(Integer, nullable=False, default=30)
    room_type = Column(String(50), default="classroom")
    is_active = Column(Boolean, nullable=False, default=True)

    sections = sa_relationship("Section", back_populates="room")


class Section(Base):
    __tablename__ = "sis_section"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    school_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_school.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_course.id", ondelete="RESTRICT"), nullable=False)
    academic_year_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_academic_year.id", ondelete="RESTRICT"), nullable=False)
    period_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_period.id", ondelete="RESTRICT"), nullable=False)
    room_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_room.id", ondelete="SET NULL"))
    teacher_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_user.id", ondelete="SET NULL"))
    section_number = Column(String(10), nullable=False, default="01")
    max_enrollment = Column(Integer, nullable=False, default=30)
    current_enrollment = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    course = sa_relationship("Course", back_populates="sections")
    room = sa_relationship("Room", back_populates="sections")
    student_sections = sa_relationship("StudentSection", back_populates="section", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_sis_section_teacher", "teacher_id", "academic_year_id"),
        Index("idx_sis_section_room", "room_id", "academic_year_id"),
        Index("idx_sis_section_period", "period_id", "academic_year_id"),
    )


class StudentSection(Base):
    __tablename__ = "sis_student_section"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_student.id", ondelete="CASCADE"), nullable=False)
    section_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_section.id", ondelete="CASCADE"), nullable=False)
    enrolled_date = Column(Date, nullable=False, server_default=func.current_date())
    dropped_date = Column(Date)
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    section = sa_relationship("Section", back_populates="student_sections")

    __table_args__ = (
        CheckConstraint(
            "status IN ('active','dropped','completed')",
            name="sis_student_section_status_check"
        ),
        Index("idx_sis_student_section_student", "student_id"),
        Index("idx_sis_student_section_section", "section_id"),
    )