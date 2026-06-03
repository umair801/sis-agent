from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class GradingScaleResponse(BaseModel):
    id: UUID
    letter_grade: str
    min_percentage: Decimal
    max_percentage: Decimal
    gpa_points: Decimal
    sort_order: int
    model_config = {"from_attributes": True}


class AssignmentCategoryCreate(BaseModel):
    section_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    weight: Decimal = Field(default=Decimal("100.0"), ge=0, le=100)
    drop_lowest: int = Field(default=0, ge=0)


class AssignmentCategoryResponse(BaseModel):
    id: UUID
    section_id: UUID
    name: str
    weight: Decimal
    drop_lowest: int
    model_config = {"from_attributes": True}


class AssignmentCreate(BaseModel):
    section_id: UUID
    category_id: Optional[UUID] = None
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    max_points: Decimal = Field(default=Decimal("100.0"), gt=0)
    due_date: Optional[date] = None
    is_published: bool = False


class AssignmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_points: Optional[Decimal] = None
    due_date: Optional[date] = None
    is_published: Optional[bool] = None


class AssignmentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    section_id: UUID
    category_id: Optional[UUID]
    name: str
    description: Optional[str]
    max_points: Decimal
    due_date: Optional[date]
    is_published: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class GradeEntry(BaseModel):
    student_id: UUID
    assignment_id: UUID
    points_earned: Optional[Decimal] = None
    is_excused: bool = False
    is_missing: bool = False
    notes: Optional[str] = None


class BulkGradeEntry(BaseModel):
    entries: List[GradeEntry] = Field(..., min_length=1)


class GradeResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    student_id: UUID
    assignment_id: UUID
    section_id: UUID
    points_earned: Optional[Decimal]
    percentage: Optional[Decimal]
    letter_grade: Optional[str]
    is_excused: bool
    is_missing: bool
    notes: Optional[str]
    graded_by: Optional[UUID]
    graded_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class SectionFinalGradeResponse(BaseModel):
    id: UUID
    student_id: UUID
    section_id: UUID
    academic_year_id: UUID
    final_percentage: Optional[Decimal]
    letter_grade: Optional[str]
    gpa_points: Optional[Decimal]
    credits_earned: Optional[Decimal]
    is_passing: bool
    computed_at: datetime
    model_config = {"from_attributes": True}


class TranscriptCourse(BaseModel):
    course_code: str
    course_name: str
    credits: Decimal
    letter_grade: Optional[str]
    gpa_points: Optional[Decimal]
    credits_earned: Optional[Decimal]
    period_name: Optional[str]


class TranscriptYear(BaseModel):
    academic_year: str
    courses: List[TranscriptCourse]
    year_gpa: Optional[Decimal]
    credits_attempted: Decimal
    credits_earned: Decimal


class TranscriptResponse(BaseModel):
    student_id: UUID
    student_number: str
    first_name: str
    last_name: str
    date_of_birth: date
    school_name: str
    cumulative_gpa: Optional[Decimal]
    total_credits_earned: Decimal
    years: List[TranscriptYear]
    generated_at: datetime


class StudentGradebookSummary(BaseModel):
    student_id: UUID
    student_number: str
    first_name: str
    last_name: str
    section_id: UUID
    final_percentage: Optional[Decimal]
    letter_grade: Optional[str]
    gpa_points: Optional[Decimal]
    is_passing: bool