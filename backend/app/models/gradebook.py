from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey,
    Index, Integer, Numeric, String, Text
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship as sa_relationship
from sqlalchemy.sql import func
from app.db.database import Base


class GradingScale(Base):
    __tablename__ = "sis_grading_scale"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    letter_grade = Column(String(5), nullable=False)
    min_percentage = Column(Numeric(5, 2), nullable=False)
    max_percentage = Column(Numeric(5, 2), nullable=False)
    gpa_points = Column(Numeric(4, 2), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)


class AssignmentCategory(Base):
    __tablename__ = "sis_assignment_category"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    section_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_section.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    weight = Column(Numeric(5, 2), nullable=False, default=100.0)
    drop_lowest = Column(Integer, nullable=False, default=0)

    assignments = sa_relationship("Assignment", back_populates="category")


class Assignment(Base):
    __tablename__ = "sis_assignment"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    section_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_section.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_assignment_category.id", ondelete="SET NULL"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    max_points = Column(Numeric(7, 2), nullable=False, default=100.0)
    due_date = Column(Date)
    is_published = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    category = sa_relationship("AssignmentCategory", back_populates="assignments")
    grades = sa_relationship("Grade", back_populates="assignment", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_sis_assignment_section", "section_id"),
    )


class Grade(Base):
    __tablename__ = "sis_grade"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_student.id", ondelete="CASCADE"), nullable=False)
    assignment_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_assignment.id", ondelete="CASCADE"), nullable=False)
    section_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_section.id", ondelete="CASCADE"), nullable=False)
    points_earned = Column(Numeric(7, 2))
    percentage = Column(Numeric(5, 2))
    letter_grade = Column(String(5))
    is_excused = Column(Boolean, nullable=False, default=False)
    is_missing = Column(Boolean, nullable=False, default=False)
    notes = Column(Text)
    graded_by = Column(PGUUID(as_uuid=True), ForeignKey("sis_user.id", ondelete="SET NULL"))
    graded_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    assignment = sa_relationship("Assignment", back_populates="grades")

    __table_args__ = (
        Index("idx_sis_grade_student", "student_id", "section_id"),
        Index("idx_sis_grade_assignment", "assignment_id"),
    )


class SectionFinalGrade(Base):
    __tablename__ = "sis_section_final_grade"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_student.id", ondelete="CASCADE"), nullable=False)
    section_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_section.id", ondelete="CASCADE"), nullable=False)
    academic_year_id = Column(PGUUID(as_uuid=True), ForeignKey("sis_academic_year.id", ondelete="CASCADE"), nullable=False)
    final_percentage = Column(Numeric(5, 2))
    letter_grade = Column(String(5))
    gpa_points = Column(Numeric(4, 2))
    credits_earned = Column(Numeric(4, 2), default=0)
    is_passing = Column(Boolean, nullable=False, default=True)
    computed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_sis_final_grade_student", "student_id", "academic_year_id"),
        Index("idx_sis_final_grade_section", "section_id"),
    )