from typing import Optional
from uuid import UUID
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_roles
from app.db.database import get_db
from app.schemas.student import (
    StudentCreate, StudentUpdate, StudentResponse, StudentListResponse,
    StudentSearchParams, PaginatedStudents,
    GuardianCreate, GuardianUpdate, GuardianResponse,
    EnrollmentCreate, EnrollmentUpdate, EnrollmentResponse,
    SchoolResponse, AcademicYearResponse, GradeLevelResponse
)
from app.services.student_service import StudentService
from app.models.user import User

router = APIRouter(prefix="/students", tags=["Students"])

ADMIN_ROLES = ["SuperAdmin", "DistrictAdmin", "Principal"]
READ_ROLES = ["SuperAdmin", "DistrictAdmin", "Principal", "Teacher", "SpEdCoordinator"]


# ------------------------------------------------------------------ #
# Lookup endpoints (no student ID required)
# ------------------------------------------------------------------ #

@router.get("/lookups/schools", response_model=list[SchoolResponse])
async def get_schools(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES))
):
    return await StudentService.get_schools(db, current_user.tenant_id)


@router.get("/lookups/academic-years", response_model=list[AcademicYearResponse])
async def get_academic_years(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES))
):
    return await StudentService.get_academic_years(db, current_user.tenant_id)


@router.get("/lookups/grade-levels", response_model=list[GradeLevelResponse])
async def get_grade_levels(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES))
):
    return await StudentService.get_grade_levels(db, current_user.tenant_id)


# ------------------------------------------------------------------ #
# Student CRUD
# ------------------------------------------------------------------ #

@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    payload: StudentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMIN_ROLES))
):
    try:
        student = await StudentService.create_student(db, current_user.tenant_id, payload)
        return student
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("", response_model=PaginatedStudents)
async def list_students(
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    grade_level_id: Optional[UUID] = Query(None),
    school_id: Optional[UUID] = Query(None),
    academic_year_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES))
):
    params = StudentSearchParams(
        search=search,
        is_active=is_active,
        grade_level_id=grade_level_id,
        school_id=school_id,
        academic_year_id=academic_year_id,
        page=page,
        page_size=page_size
    )
    students, total = await StudentService.list_students(db, current_user.tenant_id, params)
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedStudents(
        items=students,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READ_ROLES))
):
    student = await StudentService.get_student(db, current_user.tenant_id, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


@router.patch("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: UUID,
    payload: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMIN_ROLES))
):
    student = await StudentService.update_student(db, current_user.tenant_id, student_id, payload)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("SuperAdmin", "DistrictAdmin"))
):
    deleted = await StudentService.soft_delete_student(db, current_user.tenant_id, student_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")


# ------------------------------------------------------------------ #
# Guardian endpoints
# ------------------------------------------------------------------ #

@router.post("/{student_id}/guardians", response_model=GuardianResponse, status_code=status.HTTP_201_CREATED)
async def add_guardian(
    student_id: UUID,
    payload: GuardianCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMIN_ROLES))
):
    guardian = await StudentService.add_guardian(db, current_user.tenant_id, student_id, payload)
    if not guardian:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return guardian


@router.delete("/{student_id}/guardians/{guardian_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_guardian(
    student_id: UUID,
    guardian_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMIN_ROLES))
):
    deleted = await StudentService.delete_guardian(db, current_user.tenant_id, guardian_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guardian not found")


# ------------------------------------------------------------------ #
# Enrollment endpoints
# ------------------------------------------------------------------ #

@router.post("/enrollments", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def enroll_student(
    payload: EnrollmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMIN_ROLES))
):
    try:
        enrollment = await StudentService.enroll_student(db, current_user.tenant_id, payload)
        return enrollment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.patch("/enrollments/{enrollment_id}", response_model=EnrollmentResponse)
async def update_enrollment(
    enrollment_id: UUID,
    payload: EnrollmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMIN_ROLES))
):
    enrollment = await StudentService.update_enrollment(
        db, current_user.tenant_id, enrollment_id, payload
    )
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
    return enrollment