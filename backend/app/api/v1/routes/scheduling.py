from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_roles
from app.db.database import get_db
from app.schemas.scheduling import (
    CourseCreate, CourseUpdate, CourseResponse,
    RoomCreate, RoomUpdate, RoomResponse,
    SectionCreate, SectionUpdate, SectionResponse, SectionDetailResponse,
    StudentSectionCreate, StudentSectionResponse,
    ConflictCheckResult
)
from app.services.scheduling_service import SchedulingService
from app.schemas.auth import TokenPayload

router = APIRouter(prefix="/scheduling", tags=["Scheduling"])

ADMIN_ROLES = ["SuperAdmin", "DistrictAdmin", "Principal"]
READ_ROLES = ["SuperAdmin", "DistrictAdmin", "Principal", "Teacher", "SpEdCoordinator"]


# ------------------------------------------------------------------ #
# Courses
# ------------------------------------------------------------------ #

@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    payload: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ADMIN_ROLES))
):
    try:
        return await SchedulingService.create_course(db, UUID(current_user.tenant_id), payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/courses", response_model=List[CourseResponse])
async def list_courses(
    department: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*READ_ROLES))
):
    return await SchedulingService.list_courses(
        db, UUID(current_user.tenant_id), department, is_active
    )


@router.patch("/courses/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: UUID,
    payload: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ADMIN_ROLES))
):
    course = await SchedulingService.update_course(
        db, UUID(current_user.tenant_id), course_id, payload
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


# ------------------------------------------------------------------ #
# Rooms
# ------------------------------------------------------------------ #

@router.post("/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    payload: RoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ADMIN_ROLES))
):
    return await SchedulingService.create_room(db, UUID(current_user.tenant_id), payload)


@router.get("/rooms", response_model=List[RoomResponse])
async def list_rooms(
    school_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*READ_ROLES))
):
    return await SchedulingService.list_rooms(
        db, UUID(current_user.tenant_id), school_id, is_active
    )


@router.patch("/rooms/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: UUID,
    payload: RoomUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ADMIN_ROLES))
):
    room = await SchedulingService.update_room(
        db, UUID(current_user.tenant_id), room_id, payload
    )
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


# ------------------------------------------------------------------ #
# Sections
# ------------------------------------------------------------------ #

@router.post("/sections", response_model=SectionDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_section(
    payload: SectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ADMIN_ROLES))
):
    section, conflicts = await SchedulingService.create_section(
        db, UUID(current_user.tenant_id), payload
    )
    resp = SectionDetailResponse(
        id=section.id,
        tenant_id=section.tenant_id,
        school_id=section.school_id,
        course_id=section.course_id,
        academic_year_id=section.academic_year_id,
        period_id=section.period_id,
        room_id=section.room_id,
        teacher_id=section.teacher_id,
        section_number=section.section_number,
        max_enrollment=section.max_enrollment,
        current_enrollment=section.current_enrollment,
        is_active=section.is_active,
        created_at=section.created_at,
        updated_at=section.updated_at
    )
    return resp


@router.get("/sections", response_model=List[SectionDetailResponse])
async def list_sections(
    academic_year_id: Optional[UUID] = Query(None),
    school_id: Optional[UUID] = Query(None),
    teacher_id: Optional[UUID] = Query(None),
    course_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*READ_ROLES))
):
    return await SchedulingService.list_sections(
        db, UUID(current_user.tenant_id), academic_year_id, school_id, teacher_id, course_id
    )


@router.patch("/sections/{section_id}", response_model=SectionDetailResponse)
async def update_section(
    section_id: UUID,
    payload: SectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ADMIN_ROLES))
):
    section, _ = await SchedulingService.update_section(
        db, UUID(current_user.tenant_id), section_id, payload
    )
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    return SectionDetailResponse(
        id=section.id,
        tenant_id=section.tenant_id,
        school_id=section.school_id,
        course_id=section.course_id,
        academic_year_id=section.academic_year_id,
        period_id=section.period_id,
        room_id=section.room_id,
        teacher_id=section.teacher_id,
        section_number=section.section_number,
        max_enrollment=section.max_enrollment,
        current_enrollment=section.current_enrollment,
        is_active=section.is_active,
        created_at=section.created_at,
        updated_at=section.updated_at
    )


# ------------------------------------------------------------------ #
# Student section enrollment
# ------------------------------------------------------------------ #

@router.post("/student-sections", response_model=StudentSectionResponse, status_code=status.HTTP_201_CREATED)
async def enroll_student_in_section(
    payload: StudentSectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ADMIN_ROLES))
):
    try:
        ss, conflicts = await SchedulingService.enroll_student_in_section(
            db, UUID(current_user.tenant_id), payload
        )
        return ss
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/student-sections/{student_section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def drop_student_from_section(
    student_section_id: UUID,
    dropped_date: date = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ADMIN_ROLES))
):
    from datetime import date as dt
    drop_date = dropped_date or dt.today()
    dropped = await SchedulingService.drop_student_from_section(
        db, UUID(current_user.tenant_id), student_section_id, drop_date
    )
    if not dropped:
        raise HTTPException(status_code=404, detail="Student section not found")


@router.get("/student-sections/student/{student_id}", response_model=List[SectionDetailResponse])
async def get_student_schedule(
    student_id: UUID,
    academic_year_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*READ_ROLES))
):
    return await SchedulingService.get_student_schedule(
        db, UUID(current_user.tenant_id), student_id, academic_year_id
    )


# ------------------------------------------------------------------ #
# Conflict detection
# ------------------------------------------------------------------ #

@router.get("/conflicts", response_model=ConflictCheckResult)
async def detect_conflicts(
    academic_year_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*ADMIN_ROLES))
):
    return await SchedulingService.detect_conflicts(
        db, UUID(current_user.tenant_id), academic_year_id
    )