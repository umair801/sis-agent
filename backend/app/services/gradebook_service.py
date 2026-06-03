from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gradebook import (
    GradingScale, AssignmentCategory, Assignment, Grade, SectionFinalGrade
)
from app.models.scheduling import Section, Course, StudentSection
from app.models.student import Student, AcademicYear
from app.models.attendance import Period
from app.schemas.gradebook import (
    AssignmentCategoryCreate, AssignmentCreate, AssignmentUpdate,
    GradeEntry, BulkGradeEntry,
    TranscriptResponse, TranscriptYear, TranscriptCourse,
    StudentGradebookSummary
)
from app.core.logging import logger


class GradebookService:

    # ---------------------------------------------------------- #
    # Grading scale
    # ---------------------------------------------------------- #

    @staticmethod
    async def get_grading_scale(db: AsyncSession, tenant_id: UUID) -> List[GradingScale]:
        result = await db.execute(
            select(GradingScale)
            .where(GradingScale.tenant_id == tenant_id)
            .order_by(GradingScale.sort_order)
        )
        return result.scalars().all()

    @staticmethod
    async def percentage_to_letter(
        db: AsyncSession, tenant_id: UUID, percentage: Decimal
    ) -> Tuple[str, Decimal]:
        result = await db.execute(
            select(GradingScale)
            .where(
                GradingScale.tenant_id == tenant_id,
                GradingScale.min_percentage <= percentage,
                GradingScale.max_percentage >= percentage
            )
            .order_by(GradingScale.sort_order)
            .limit(1)
        )
        scale = result.scalar_one_or_none()
        if scale:
            return scale.letter_grade, scale.gpa_points
        return "F", Decimal("0.00")

    # ---------------------------------------------------------- #
    # Assignment categories
    # ---------------------------------------------------------- #

    @staticmethod
    async def create_category(
        db: AsyncSession, tenant_id: UUID, payload: AssignmentCategoryCreate
    ) -> AssignmentCategory:
        existing = await db.execute(
            select(AssignmentCategory).where(
                AssignmentCategory.section_id == payload.section_id,
                AssignmentCategory.name == payload.name
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Category '{payload.name}' already exists in this section")
        cat = AssignmentCategory(tenant_id=tenant_id, **payload.model_dump())
        db.add(cat)
        await db.commit()
        await db.refresh(cat)
        return cat

    @staticmethod
    async def get_categories(
        db: AsyncSession, tenant_id: UUID, section_id: UUID
    ) -> List[AssignmentCategory]:
        result = await db.execute(
            select(AssignmentCategory).where(
                AssignmentCategory.tenant_id == tenant_id,
                AssignmentCategory.section_id == section_id
            )
        )
        return result.scalars().all()

    # ---------------------------------------------------------- #
    # Assignments
    # ---------------------------------------------------------- #

    @staticmethod
    async def create_assignment(
        db: AsyncSession, tenant_id: UUID, payload: AssignmentCreate
    ) -> Assignment:
        assignment = Assignment(tenant_id=tenant_id, **payload.model_dump())
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)
        return assignment

    @staticmethod
    async def list_assignments(
        db: AsyncSession, tenant_id: UUID, section_id: UUID
    ) -> List[Assignment]:
        result = await db.execute(
            select(Assignment)
            .where(Assignment.tenant_id == tenant_id, Assignment.section_id == section_id)
            .order_by(Assignment.due_date, Assignment.name)
        )
        return result.scalars().all()

    @staticmethod
    async def update_assignment(
        db: AsyncSession, tenant_id: UUID, assignment_id: UUID, payload: AssignmentUpdate
    ) -> Optional[Assignment]:
        result = await db.execute(
            select(Assignment).where(
                Assignment.id == assignment_id, Assignment.tenant_id == tenant_id
            )
        )
        assignment = result.scalar_one_or_none()
        if not assignment:
            return None
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(assignment, field, value)
        await db.commit()
        await db.refresh(assignment)
        return assignment

    # ---------------------------------------------------------- #
    # Grade entry
    # ---------------------------------------------------------- #

    @staticmethod
    async def upsert_grade(
        db: AsyncSession,
        tenant_id: UUID,
        graded_by: UUID,
        entry: GradeEntry
    ) -> Grade:
        assignment_result = await db.execute(
            select(Assignment).where(Assignment.id == entry.assignment_id)
        )
        assignment = assignment_result.scalar_one_or_none()
        if not assignment:
            raise ValueError(f"Assignment {entry.assignment_id} not found")

        percentage = None
        letter_grade = None
        if entry.points_earned is not None and not entry.is_excused:
            percentage = round(
                float(entry.points_earned) / float(assignment.max_points) * 100, 2
            )
            letter_grade, _ = await GradebookService.percentage_to_letter(
                db, tenant_id, Decimal(str(percentage))
            )

        existing_result = await db.execute(
            select(Grade).where(
                Grade.student_id == entry.student_id,
                Grade.assignment_id == entry.assignment_id
            )
        )
        existing = existing_result.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if existing:
            existing.points_earned = entry.points_earned
            existing.percentage = percentage
            existing.letter_grade = letter_grade
            existing.is_excused = entry.is_excused
            existing.is_missing = entry.is_missing
            existing.notes = entry.notes
            existing.graded_by = graded_by
            existing.graded_at = now
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            grade = Grade(
                tenant_id=tenant_id,
                student_id=entry.student_id,
                assignment_id=entry.assignment_id,
                section_id=assignment.section_id,
                points_earned=entry.points_earned,
                percentage=percentage,
                letter_grade=letter_grade,
                is_excused=entry.is_excused,
                is_missing=entry.is_missing,
                notes=entry.notes,
                graded_by=graded_by,
                graded_at=now
            )
            db.add(grade)
            await db.commit()
            await db.refresh(grade)
            return grade

    @staticmethod
    async def bulk_enter_grades(
        db: AsyncSession,
        tenant_id: UUID,
        graded_by: UUID,
        payload: BulkGradeEntry
    ) -> List[Grade]:
        grades = []
        for entry in payload.entries:
            grade = await GradebookService.upsert_grade(db, tenant_id, graded_by, entry)
            grades.append(grade)
        logger.info(f"Bulk grade entry: {len(grades)} grades by {graded_by}")
        return grades

    @staticmethod
    async def get_grades_for_section(
        db: AsyncSession, tenant_id: UUID, section_id: UUID,
        student_id: Optional[UUID] = None
    ) -> List[Grade]:
        query = select(Grade).where(
            Grade.tenant_id == tenant_id,
            Grade.section_id == section_id
        )
        if student_id:
            query = query.where(Grade.student_id == student_id)
        result = await db.execute(query.order_by(Grade.student_id))
        return result.scalars().all()

    # ---------------------------------------------------------- #
    # GPA computation
    # ---------------------------------------------------------- #

    @staticmethod
    async def compute_section_final_grade(
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID,
        section_id: UUID,
        academic_year_id: UUID
    ) -> SectionFinalGrade:
        grades_result = await db.execute(
            select(Grade, Assignment.max_points, AssignmentCategory.weight)
            .join(Assignment, Assignment.id == Grade.assignment_id)
            .outerjoin(AssignmentCategory, AssignmentCategory.id == Assignment.category_id)
            .where(
                Grade.tenant_id == tenant_id,
                Grade.student_id == student_id,
                Grade.section_id == section_id,
                Grade.is_excused == False
            )
        )
        rows = grades_result.all()

        if not rows:
            return None

        total_points = sum(
            float(r.Grade.points_earned or 0) for r in rows if not r.Grade.is_missing
        )
        total_max = sum(
            float(r.max_points) for r in rows if not r.Grade.is_missing
        )

        if total_max == 0:
            return None

        final_pct = round(total_points / total_max * 100, 2)
        letter, gpa_pts = await GradebookService.percentage_to_letter(
            db, tenant_id, Decimal(str(final_pct))
        )

        section_result = await db.execute(
            select(Section.id, Course.credits.label("credits"))
            .join(Course, Course.id == Section.course_id)
            .where(Section.id == section_id)
        )
        section_row = section_result.first()
        credits = Decimal(str(section_row.credits)) if section_row and section_row.credits else Decimal("1.0")

        is_passing = final_pct >= 60.0
        credits_earned = credits if is_passing else Decimal("0.0")

        existing_result = await db.execute(
            select(SectionFinalGrade).where(
                SectionFinalGrade.student_id == student_id,
                SectionFinalGrade.section_id == section_id
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            existing.final_percentage = Decimal(str(final_pct))
            existing.letter_grade = letter
            existing.gpa_points = gpa_pts
            existing.credits_earned = credits_earned
            existing.is_passing = is_passing
            existing.computed_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            fg = SectionFinalGrade(
                tenant_id=tenant_id,
                student_id=student_id,
                section_id=section_id,
                academic_year_id=academic_year_id,
                final_percentage=Decimal(str(final_pct)),
                letter_grade=letter,
                gpa_points=gpa_pts,
                credits_earned=credits_earned,
                is_passing=is_passing
            )
            db.add(fg)
            await db.commit()
            await db.refresh(fg)
            return fg

    @staticmethod
    async def get_section_gradebook(
        db: AsyncSession,
        tenant_id: UUID,
        section_id: UUID,
        academic_year_id: UUID
    ) -> List[StudentGradebookSummary]:
        result = await db.execute(
            select(
                SectionFinalGrade.student_id,
                SectionFinalGrade.section_id,
                SectionFinalGrade.final_percentage,
                SectionFinalGrade.letter_grade,
                SectionFinalGrade.gpa_points,
                SectionFinalGrade.is_passing,
                Student.student_number,
                Student.first_name,
                Student.last_name
            )
            .join(Student, Student.id == SectionFinalGrade.student_id)
            .where(
                SectionFinalGrade.tenant_id == tenant_id,
                SectionFinalGrade.section_id == section_id,
                SectionFinalGrade.academic_year_id == academic_year_id
            )
            .order_by(Student.last_name, Student.first_name)
        )
        rows = result.all()
        return [
            StudentGradebookSummary(
                student_id=row.student_id,
                student_number=row.student_number,
                first_name=row.first_name,
                last_name=row.last_name,
                section_id=row.section_id,
                final_percentage=row.final_percentage,
                letter_grade=row.letter_grade,
                gpa_points=row.gpa_points,
                is_passing=row.is_passing
            )
            for row in rows
        ]

    # ---------------------------------------------------------- #
    # Transcript generation
    # ---------------------------------------------------------- #

    @staticmethod
    async def generate_transcript(
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID
    ) -> TranscriptResponse:
        student_result = await db.execute(
            select(Student).where(
                Student.id == student_id,
                Student.tenant_id == tenant_id
            )
        )
        student = student_result.scalar_one_or_none()
        if not student:
            raise ValueError("Student not found")

        fg_result = await db.execute(
            select(
                SectionFinalGrade.final_percentage,
                SectionFinalGrade.letter_grade,
                SectionFinalGrade.gpa_points,
                SectionFinalGrade.credits_earned,
                SectionFinalGrade.academic_year_id,
                SectionFinalGrade.section_id,
                Course.course_code,
                Course.name.label("course_name"),
                Course.credits,
                AcademicYear.name.label("year_name"),
                Period.name.label("period_name")
            )
            .join(Section, Section.id == SectionFinalGrade.section_id)
            .join(Course, Course.id == Section.course_id)
            .join(AcademicYear, AcademicYear.id == SectionFinalGrade.academic_year_id)
            .join(Period, Period.id == Section.period_id)
            .where(
                SectionFinalGrade.tenant_id == tenant_id,
                SectionFinalGrade.student_id == student_id
            )
            .order_by(AcademicYear.start_date, Period.sort_order)
        )
        fg_rows = fg_result.all()

        years_map = {}
        for row in fg_rows:
            yr = row.year_name
            if yr not in years_map:
                years_map[yr] = []
            years_map[yr].append(row)

        transcript_years = []
        total_gpa_points = Decimal("0")
        total_credits_for_gpa = Decimal("0")
        total_credits_earned = Decimal("0")

        for year_name, rows in years_map.items():
            courses = []
            year_gpa_num = Decimal("0")
            year_credits = Decimal("0")
            year_earned = Decimal("0")

            for row in rows:
                courses.append(TranscriptCourse(
                    course_code=row.course_code,
                    course_name=row.course_name,
                    credits=row.credits,
                    letter_grade=row.letter_grade,
                    gpa_points=row.gpa_points,
                    credits_earned=row.credits_earned,
                    period_name=row.period_name
                ))
                if row.gpa_points is not None and row.credits:
                    year_gpa_num += Decimal(str(row.gpa_points)) * Decimal(str(row.credits))
                    year_credits += Decimal(str(row.credits))
                if row.credits_earned:
                    year_earned += Decimal(str(row.credits_earned))

            year_gpa = round(year_gpa_num / year_credits, 2) if year_credits > 0 else None
            total_gpa_points += year_gpa_num
            total_credits_for_gpa += year_credits
            total_credits_earned += year_earned

            transcript_years.append(TranscriptYear(
                academic_year=year_name,
                courses=courses,
                year_gpa=year_gpa,
                credits_attempted=year_credits,
                credits_earned=year_earned
            ))

        cumulative_gpa = (
            round(total_gpa_points / total_credits_for_gpa, 2)
            if total_credits_for_gpa > 0 else None
        )

        return TranscriptResponse(
            student_id=student.id,
            student_number=student.student_number,
            first_name=student.first_name,
            last_name=student.last_name,
            date_of_birth=student.date_of_birth,
            school_name="Westlake High School",
            cumulative_gpa=cumulative_gpa,
            total_credits_earned=total_credits_earned,
            years=transcript_years,
            generated_at=datetime.now(timezone.utc)
        )