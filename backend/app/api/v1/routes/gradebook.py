from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_roles
from app.db.database import get_db
from app.schemas.gradebook import (
    GradingScaleResponse,
    AssignmentCategoryCreate, AssignmentCategoryResponse,
    AssignmentCreate, AssignmentUpdate, AssignmentResponse,
    GradeEntry, BulkGradeEntry, GradeResponse,
    SectionFinalGradeResponse, TranscriptResponse,
    StudentGradebookSummary
)
from app.services.gradebook_service import GradebookService
from app.schemas.auth import TokenPayload

router = APIRouter(prefix="/gradebook", tags=["Gradebook"])

TEACHER_ROLES = ["SuperAdmin", "DistrictAdmin", "Principal", "Teacher"]
READ_ROLES = ["SuperAdmin", "DistrictAdmin", "Principal", "Teacher", "SpEdCoordinator"]
ADMIN_ROLES = ["SuperAdmin", "DistrictAdmin", "Principal"]


@router.get("/grading-scale", response_model=List[GradingScaleResponse])
async def get_grading_scale(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*READ_ROLES))
):
    return await GradebookService.get_grading_scale(db, UUID(current_user.tenant_id))


@router.post("/categories", response_model=AssignmentCategoryResponse, status_code=201)
async def create_category(
    payload: AssignmentCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*TEACHER_ROLES))
):
    try:
        return await GradebookService.create_category(db, UUID(current_user.tenant_id), payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/categories", response_model=List[AssignmentCategoryResponse])
async def get_categories(
    section_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*READ_ROLES))
):
    return await GradebookService.get_categories(db, UUID(current_user.tenant_id), section_id)


@router.post("/assignments", response_model=AssignmentResponse, status_code=201)
async def create_assignment(
    payload: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*TEACHER_ROLES))
):
    return await GradebookService.create_assignment(db, UUID(current_user.tenant_id), payload)


@router.get("/assignments", response_model=List[AssignmentResponse])
async def list_assignments(
    section_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*READ_ROLES))
):
    return await GradebookService.list_assignments(db, UUID(current_user.tenant_id), section_id)


@router.patch("/assignments/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: UUID,
    payload: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*TEACHER_ROLES))
):
    assignment = await GradebookService.update_assignment(
        db, UUID(current_user.tenant_id), assignment_id, payload
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.post("/grades", response_model=GradeResponse, status_code=201)
async def enter_grade(
    payload: GradeEntry,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*TEACHER_ROLES))
):
    try:
        return await GradebookService.upsert_grade(
            db, UUID(current_user.tenant_id), UUID(current_user.sub), payload
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/grades/bulk", response_model=List[GradeResponse])
async def bulk_enter_grades(
    payload: BulkGradeEntry,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*TEACHER_ROLES))
):
    return await GradebookService.bulk_enter_grades(
        db, UUID(current_user.tenant_id), UUID(current_user.sub), payload
    )


@router.get("/grades", response_model=List[GradeResponse])
async def get_grades(
    section_id: UUID = Query(...),
    student_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*READ_ROLES))
):
    return await GradebookService.get_grades_for_section(
        db, UUID(current_user.tenant_id), section_id, student_id
    )


@router.post("/final-grades/compute", response_model=SectionFinalGradeResponse)
async def compute_final_grade(
    student_id: UUID = Query(...),
    section_id: UUID = Query(...),
    academic_year_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*TEACHER_ROLES))
):
    fg = await GradebookService.compute_section_final_grade(
        db, UUID(current_user.tenant_id), student_id, section_id, academic_year_id
    )
    if not fg:
        raise HTTPException(status_code=404, detail="No grades found to compute")
    return fg


@router.get("/final-grades", response_model=List[StudentGradebookSummary])
async def get_section_gradebook(
    section_id: UUID = Query(...),
    academic_year_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*READ_ROLES))
):
    return await GradebookService.get_section_gradebook(
        db, UUID(current_user.tenant_id), section_id, academic_year_id
    )


@router.get("/transcript/{student_id}", response_model=TranscriptResponse)
async def get_transcript(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*READ_ROLES))
):
    try:
        return await GradebookService.generate_transcript(
            db, UUID(current_user.tenant_id), student_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))