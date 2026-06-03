from datetime import date, datetime, timezone
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.student import (
    Student, Guardian, Enrollment, School, AcademicYear, GradeLevel
)
from app.schemas.student import (
    StudentCreate, StudentUpdate, EnrollmentCreate, EnrollmentUpdate,
    StudentSearchParams
)
from app.core.logging import logger


class StudentService:

    # ---------------------------------------------------------- #
    # Student CRUD
    # ---------------------------------------------------------- #

    @staticmethod
    async def create_student(
        db: AsyncSession,
        tenant_id: UUID,
        payload: StudentCreate
    ) -> Student:
        # Check for duplicate student number within tenant
        existing = await db.execute(
            select(Student).where(
                Student.tenant_id == tenant_id,
                Student.student_number == payload.student_number,
                Student.is_deleted == False
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Student number '{payload.student_number}' already exists in this district")

        guardian_data = payload.guardians or []
        student_data = payload.model_dump(exclude={"guardians"})
        student_data["tenant_id"] = tenant_id

        student = Student(**student_data)
        db.add(student)
        await db.flush()  # get student.id before inserting guardians

        for g in guardian_data:
            guardian = Guardian(
                tenant_id=tenant_id,
                student_id=student.id,
                **g.model_dump()
            )
            db.add(guardian)

        await db.commit()
        await db.refresh(student)

        result = await db.execute(
            select(Student)
            .options(selectinload(Student.guardians))
            .where(Student.id == student.id)
        )
        return result.scalar_one()

    @staticmethod
    async def get_student(
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID
    ) -> Optional[Student]:
        result = await db.execute(
            select(Student)
            .options(selectinload(Student.guardians))
            .where(
                Student.id == student_id,
                Student.tenant_id == tenant_id,
                Student.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_students(
        db: AsyncSession,
        tenant_id: UUID,
        params: StudentSearchParams
    ) -> Tuple[List[Student], int]:
        base_query = select(Student).where(
            Student.tenant_id == tenant_id,
            Student.is_deleted == False
        )

        if params.is_active is not None:
            base_query = base_query.where(Student.is_active == params.is_active)

        if params.search:
            term = f"%{params.search}%"
            base_query = base_query.where(
                or_(
                    Student.first_name.ilike(term),
                    Student.last_name.ilike(term),
                    Student.student_number.ilike(term),
                    Student.email.ilike(term)
                )
            )

        if params.grade_level_id or params.school_id or params.academic_year_id:
            base_query = base_query.join(
                Enrollment,
                and_(
                    Enrollment.student_id == Student.id,
                    Enrollment.tenant_id == tenant_id,
                    Enrollment.status == "active"
                )
            )
            if params.grade_level_id:
                base_query = base_query.where(Enrollment.grade_level_id == params.grade_level_id)
            if params.school_id:
                base_query = base_query.where(Enrollment.school_id == params.school_id)
            if params.academic_year_id:
                base_query = base_query.where(Enrollment.academic_year_id == params.academic_year_id)

        count_result = await db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar_one()

        offset = (params.page - 1) * params.page_size
        base_query = base_query.order_by(Student.last_name, Student.first_name)
        base_query = base_query.offset(offset).limit(params.page_size)

        result = await db.execute(base_query)
        students = result.scalars().all()

        return students, total

    @staticmethod
    async def update_student(
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID,
        payload: StudentUpdate
    ) -> Optional[Student]:
        result = await db.execute(
            select(Student).where(
                Student.id == student_id,
                Student.tenant_id == tenant_id,
                Student.is_deleted == False
            )
        )
        student = result.scalar_one_or_none()
        if not student:
            return None

        update_data = payload.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(student, field, value)

        await db.commit()
        await db.refresh(student)

        full = await db.execute(
            select(Student)
            .options(selectinload(Student.guardians))
            .where(Student.id == student_id)
        )
        return full.scalar_one()

    @staticmethod
    async def soft_delete_student(
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID
    ) -> bool:
        result = await db.execute(
            select(Student).where(
                Student.id == student_id,
                Student.tenant_id == tenant_id,
                Student.is_deleted == False
            )
        )
        student = result.scalar_one_or_none()
        if not student:
            return False

        student.is_deleted = True
        student.is_active = False
        student.deleted_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(f"Student {student_id} soft-deleted by tenant {tenant_id}")
        return True

    # ---------------------------------------------------------- #
    # Guardian CRUD
    # ---------------------------------------------------------- #

    @staticmethod
    async def add_guardian(
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID,
        payload
    ) -> Optional[Guardian]:
        student_check = await db.execute(
            select(Student.id).where(
                Student.id == student_id,
                Student.tenant_id == tenant_id,
                Student.is_deleted == False
            )
        )
        if not student_check.scalar_one_or_none():
            return None

        guardian = Guardian(
            tenant_id=tenant_id,
            student_id=student_id,
            **payload.model_dump()
        )
        db.add(guardian)
        await db.commit()
        await db.refresh(guardian)
        return guardian

    @staticmethod
    async def delete_guardian(
        db: AsyncSession,
        tenant_id: UUID,
        guardian_id: UUID
    ) -> bool:
        result = await db.execute(
            select(Guardian).where(
                Guardian.id == guardian_id,
                Guardian.tenant_id == tenant_id
            )
        )
        guardian = result.scalar_one_or_none()
        if not guardian:
            return False
        await db.delete(guardian)
        await db.commit()
        return True

    # ---------------------------------------------------------- #
    # Enrollment CRUD
    # ---------------------------------------------------------- #

    @staticmethod
    async def enroll_student(
        db: AsyncSession,
        tenant_id: UUID,
        payload: EnrollmentCreate
    ) -> Enrollment:
        existing = await db.execute(
            select(Enrollment).where(
                Enrollment.tenant_id == tenant_id,
                Enrollment.student_id == payload.student_id,
                Enrollment.academic_year_id == payload.academic_year_id
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Student is already enrolled for this academic year")

        enrollment = Enrollment(
            tenant_id=tenant_id,
            **payload.model_dump()
        )
        db.add(enrollment)
        await db.commit()
        await db.refresh(enrollment)
        return enrollment

    @staticmethod
    async def update_enrollment(
        db: AsyncSession,
        tenant_id: UUID,
        enrollment_id: UUID,
        payload: EnrollmentUpdate
    ) -> Optional[Enrollment]:
        result = await db.execute(
            select(Enrollment).where(
                Enrollment.id == enrollment_id,
                Enrollment.tenant_id == tenant_id
            )
        )
        enrollment = result.scalar_one_or_none()
        if not enrollment:
            return None

        update_data = payload.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(enrollment, field, value)

        await db.commit()
        await db.refresh(enrollment)
        return enrollment

    # ---------------------------------------------------------- #
    # Lookups
    # ---------------------------------------------------------- #

    @staticmethod
    async def get_schools(db: AsyncSession, tenant_id: UUID) -> List[School]:
        result = await db.execute(
            select(School).where(
                School.tenant_id == tenant_id,
                School.is_active == True
            ).order_by(School.name)
        )
        return result.scalars().all()

    @staticmethod
    async def get_academic_years(db: AsyncSession, tenant_id: UUID) -> List[AcademicYear]:
        result = await db.execute(
            select(AcademicYear).where(
                AcademicYear.tenant_id == tenant_id
            ).order_by(AcademicYear.start_date.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_grade_levels(db: AsyncSession, tenant_id: UUID) -> List[GradeLevel]:
        result = await db.execute(
            select(GradeLevel).where(
                GradeLevel.tenant_id == tenant_id
            ).order_by(GradeLevel.sort_order)
        )
        return result.scalars().all()