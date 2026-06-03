from datetime import date, datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator


# ------------------------------------------------------------------ #
# Guardian schemas
# ------------------------------------------------------------------ #

class GuardianBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    relationship: str = Field(..., min_length=1, max_length=50)
    phone_primary: Optional[str] = Field(None, max_length=30)
    phone_secondary: Optional[str] = Field(None, max_length=30)
    email: Optional[EmailStr] = None
    is_emergency_contact: bool = False
    is_authorized_pickup: bool = False


class GuardianCreate(GuardianBase):
    pass


class GuardianUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    relationship: Optional[str] = Field(None, max_length=50)
    phone_primary: Optional[str] = Field(None, max_length=30)
    phone_secondary: Optional[str] = Field(None, max_length=30)
    email: Optional[EmailStr] = None
    is_emergency_contact: Optional[bool] = None
    is_authorized_pickup: Optional[bool] = None


class GuardianResponse(GuardianBase):
    id: UUID
    student_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ------------------------------------------------------------------ #
# Student schemas
# ------------------------------------------------------------------ #

class StudentBase(BaseModel):
    student_number: str = Field(..., min_length=1, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: Optional[str] = Field(None, max_length=20)
    ethnicity: Optional[str] = Field(None, max_length=50)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[EmailStr] = None
    photo_url: Optional[str] = None

    @field_validator("date_of_birth")
    @classmethod
    def dob_not_future(cls, v: date) -> date:
        from datetime import date as dt
        if v > dt.today():
            raise ValueError("Date of birth cannot be in the future")
        return v


class StudentCreate(StudentBase):
    guardians: Optional[List[GuardianCreate]] = []


class StudentUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    ethnicity: Optional[str] = Field(None, max_length=50)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[EmailStr] = None
    photo_url: Optional[str] = None
    is_active: Optional[bool] = None


class StudentResponse(StudentBase):
    id: UUID
    tenant_id: UUID
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    guardians: List[GuardianResponse] = []

    model_config = {"from_attributes": True}


class StudentListResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    student_number: str
    first_name: str
    middle_name: Optional[str]
    last_name: str
    date_of_birth: date
    gender: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class StudentSearchParams(BaseModel):
    search: Optional[str] = None
    is_active: Optional[bool] = True
    grade_level_id: Optional[UUID] = None
    school_id: Optional[UUID] = None
    academic_year_id: Optional[UUID] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# ------------------------------------------------------------------ #
# Enrollment schemas
# ------------------------------------------------------------------ #

class EnrollmentCreate(BaseModel):
    student_id: UUID
    school_id: UUID
    academic_year_id: UUID
    grade_level_id: UUID
    enrollment_date: date
    homeroom_teacher_id: Optional[UUID] = None


class EnrollmentUpdate(BaseModel):
    grade_level_id: Optional[UUID] = None
    homeroom_teacher_id: Optional[UUID] = None
    status: Optional[str] = None
    withdrawal_date: Optional[date] = None
    withdrawal_reason: Optional[str] = Field(None, max_length=255)


class EnrollmentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    student_id: UUID
    school_id: UUID
    academic_year_id: UUID
    grade_level_id: UUID
    enrollment_date: date
    withdrawal_date: Optional[date]
    withdrawal_reason: Optional[str]
    status: str
    homeroom_teacher_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ------------------------------------------------------------------ #
# Lookup schemas
# ------------------------------------------------------------------ #

class SchoolResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    short_name: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    principal_name: Optional[str]
    is_active: bool

    model_config = {"from_attributes": True}


class AcademicYearResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    start_date: date
    end_date: date
    is_current: bool

    model_config = {"from_attributes": True}


class GradeLevelResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    short_name: str
    sort_order: int

    model_config = {"from_attributes": True}


# ------------------------------------------------------------------ #
# Paginated response wrapper
# ------------------------------------------------------------------ #

class PaginatedStudents(BaseModel):
    items: List[StudentListResponse]
    total: int
    page: int
    page_size: int
    total_pages: int