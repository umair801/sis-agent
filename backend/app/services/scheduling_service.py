from datetime import date
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scheduling import Course, Room, Section, StudentSection
from app.models.attendance import Period
from app.models.student import Student
from app.schemas.scheduling import (
    CourseCreate, CourseUpdate,
    RoomCreate, RoomUpdate,
    SectionCreate, SectionUpdate,
    StudentSectionCreate,
    ScheduleConflict, ConflictCheckResult,
    SectionDetailResponse
)
from app.core.logging import logger


class SchedulingService:

    # ---------------------------------------------------------- #
    # Courses
    # ---------------------------------------------------------- #

    @staticmethod
    async def create_course(db: AsyncSession, tenant_id: UUID, payload: CourseCreate) -> Course:
        existing = await db.execute(
            select(Course).where(
                Course.tenant_id == tenant_id,
                Course.course_code == payload.course_code
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Course code '{payload.course_code}' already exists")
        course = Course(tenant_id=tenant_id, **payload.model_dump())
        db.add(course)
        await db.commit()
        await db.refresh(course)
        return course

    @staticmethod
    async def list_courses(
        db: AsyncSession,
        tenant_id: UUID,
        department: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> List[Course]:
        query = select(Course).where(Course.tenant_id == tenant_id)
        if is_active is not None:
            query = query.where(Course.is_active == is_active)
        if department:
            query = query.where(Course.department == department)
        result = await db.execute(query.order_by(Course.department, Course.course_code))
        return result.scalars().all()

    @staticmethod
    async def update_course(
        db: AsyncSession, tenant_id: UUID, course_id: UUID, payload: CourseUpdate
    ) -> Optional[Course]:
        result = await db.execute(
            select(Course).where(Course.id == course_id, Course.tenant_id == tenant_id)
        )
        course = result.scalar_one_or_none()
        if not course:
            return None
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(course, field, value)
        await db.commit()
        await db.refresh(course)
        return course

    # ---------------------------------------------------------- #
    # Rooms
    # ---------------------------------------------------------- #

    @staticmethod
    async def create_room(db: AsyncSession, tenant_id: UUID, payload: RoomCreate) -> Room:
        room = Room(tenant_id=tenant_id, **payload.model_dump())
        db.add(room)
        await db.commit()
        await db.refresh(room)
        return room

    @staticmethod
    async def list_rooms(
        db: AsyncSession,
        tenant_id: UUID,
        school_id: Optional[UUID] = None,
        is_active: Optional[bool] = True
    ) -> List[Room]:
        query = select(Room).where(Room.tenant_id == tenant_id)
        if is_active is not None:
            query = query.where(Room.is_active == is_active)
        if school_id:
            query = query.where(Room.school_id == school_id)
        result = await db.execute(query.order_by(Room.name))
        return result.scalars().all()

    @staticmethod
    async def update_room(
        db: AsyncSession, tenant_id: UUID, room_id: UUID, payload: RoomUpdate
    ) -> Optional[Room]:
        result = await db.execute(
            select(Room).where(Room.id == room_id, Room.tenant_id == tenant_id)
        )
        room = result.scalar_one_or_none()
        if not room:
            return None
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(room, field, value)
        await db.commit()
        await db.refresh(room)
        return room

    # ---------------------------------------------------------- #
    # Sections
    # ---------------------------------------------------------- #

    @staticmethod
    async def create_section(
        db: AsyncSession, tenant_id: UUID, payload: SectionCreate
    ) -> Tuple[Section, List[ScheduleConflict]]:
        # Check for conflicts before creating
        conflicts = await SchedulingService._check_new_section_conflicts(
            db, tenant_id, payload
        )
        hard_conflicts = [c for c in conflicts if c.severity == "error"]

        section = Section(tenant_id=tenant_id, **payload.model_dump())
        db.add(section)
        await db.commit()
        await db.refresh(section)

        if hard_conflicts:
            logger.info(f"Section {section.id} created with {len(hard_conflicts)} conflict(s)")

        return section, conflicts

    @staticmethod
    async def list_sections(
        db: AsyncSession,
        tenant_id: UUID,
        academic_year_id: Optional[UUID] = None,
        school_id: Optional[UUID] = None,
        teacher_id: Optional[UUID] = None,
        course_id: Optional[UUID] = None
    ) -> List[SectionDetailResponse]:
        query = (
            select(
                Section.id,
                Section.tenant_id,
                Section.school_id,
                Section.course_id,
                Section.academic_year_id,
                Section.period_id,
                Section.room_id,
                Section.teacher_id,
                Section.section_number,
                Section.max_enrollment,
                Section.current_enrollment,
                Section.is_active,
                Section.created_at,
                Section.updated_at,
                Course.course_code,
                Course.name.label("course_name"),
                Period.name.label("period_name"),
                Room.name.label("room_name"),
            )
            .join(Course, Course.id == Section.course_id)
            .join(Period, Period.id == Section.period_id)
            .outerjoin(Room, Room.id == Section.room_id)
            .where(Section.tenant_id == tenant_id, Section.is_active == True)
        )
        if academic_year_id:
            query = query.where(Section.academic_year_id == academic_year_id)
        if school_id:
            query = query.where(Section.school_id == school_id)
        if teacher_id:
            query = query.where(Section.teacher_id == teacher_id)
        if course_id:
            query = query.where(Section.course_id == course_id)

        result = await db.execute(query.order_by(Period.sort_order, Course.course_code))
        rows = result.all()

        return [
            SectionDetailResponse(
                id=row.id,
                tenant_id=row.tenant_id,
                school_id=row.school_id,
                course_id=row.course_id,
                academic_year_id=row.academic_year_id,
                period_id=row.period_id,
                room_id=row.room_id,
                teacher_id=row.teacher_id,
                section_number=row.section_number,
                max_enrollment=row.max_enrollment,
                current_enrollment=row.current_enrollment,
                is_active=row.is_active,
                created_at=row.created_at,
                updated_at=row.updated_at,
                course_code=row.course_code,
                course_name=row.course_name,
                period_name=row.period_name,
                room_name=row.room_name,
            )
            for row in rows
        ]

    @staticmethod
    async def update_section(
        db: AsyncSession, tenant_id: UUID, section_id: UUID, payload: SectionUpdate
    ) -> Tuple[Optional[Section], List[ScheduleConflict]]:
        result = await db.execute(
            select(Section).where(Section.id == section_id, Section.tenant_id == tenant_id)
        )
        section = result.scalar_one_or_none()
        if not section:
            return None, []

        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(section, field, value)

        await db.commit()
        await db.refresh(section)

        conflicts = await SchedulingService.detect_conflicts(
            db, tenant_id, section.academic_year_id
        )
        return section, conflicts.conflicts

    # ---------------------------------------------------------- #
    # Student section enrollment
    # ---------------------------------------------------------- #

    @staticmethod
    async def enroll_student_in_section(
        db: AsyncSession, tenant_id: UUID, payload: StudentSectionCreate
    ) -> Tuple[StudentSection, List[ScheduleConflict]]:
        # Check duplicate
        existing = await db.execute(
            select(StudentSection).where(
                StudentSection.tenant_id == tenant_id,
                StudentSection.student_id == payload.student_id,
                StudentSection.section_id == payload.section_id
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Student is already enrolled in this section")

        # Check section capacity
        section_result = await db.execute(
            select(Section).where(Section.id == payload.section_id, Section.tenant_id == tenant_id)
        )
        section = section_result.scalar_one_or_none()
        if not section:
            raise ValueError("Section not found")
        if section.current_enrollment >= section.max_enrollment:
            raise ValueError(f"Section is full ({section.current_enrollment}/{section.max_enrollment})")

        # Check student period conflict
        conflicts = await SchedulingService._check_student_period_conflict(
            db, tenant_id, payload.student_id, section
        )

        enroll_date = payload.enrolled_date or date.today()
        student_section = StudentSection(
            tenant_id=tenant_id,
            student_id=payload.student_id,
            section_id=payload.section_id,
            enrolled_date=enroll_date
        )
        db.add(student_section)

        section.current_enrollment += 1
        await db.commit()
        await db.refresh(student_section)

        return student_section, conflicts

    @staticmethod
    async def drop_student_from_section(
        db: AsyncSession, tenant_id: UUID, student_section_id: UUID, dropped_date: date
    ) -> bool:
        result = await db.execute(
            select(StudentSection).where(
                StudentSection.id == student_section_id,
                StudentSection.tenant_id == tenant_id
            )
        )
        ss = result.scalar_one_or_none()
        if not ss:
            return False

        ss.status = "dropped"
        ss.dropped_date = dropped_date

        section_result = await db.execute(
            select(Section).where(Section.id == ss.section_id)
        )
        section = section_result.scalar_one_or_none()
        if section and section.current_enrollment > 0:
            section.current_enrollment -= 1

        await db.commit()
        return True

    @staticmethod
    async def get_student_schedule(
        db: AsyncSession, tenant_id: UUID, student_id: UUID, academic_year_id: UUID
    ) -> List[SectionDetailResponse]:
        query = (
            select(
                Section.id,
                Section.tenant_id,
                Section.school_id,
                Section.course_id,
                Section.academic_year_id,
                Section.period_id,
                Section.room_id,
                Section.teacher_id,
                Section.section_number,
                Section.max_enrollment,
                Section.current_enrollment,
                Section.is_active,
                Section.created_at,
                Section.updated_at,
                Course.course_code,
                Course.name.label("course_name"),
                Period.name.label("period_name"),
                Room.name.label("room_name"),
            )
            .join(StudentSection, StudentSection.section_id == Section.id)
            .join(Course, Course.id == Section.course_id)
            .join(Period, Period.id == Section.period_id)
            .outerjoin(Room, Room.id == Section.room_id)
            .where(
                StudentSection.tenant_id == tenant_id,
                StudentSection.student_id == student_id,
                StudentSection.status == "active",
                Section.academic_year_id == academic_year_id
            )
            .order_by(Period.sort_order)
        )
        result = await db.execute(query)
        rows = result.all()

        return [
            SectionDetailResponse(
                id=row.id,
                tenant_id=row.tenant_id,
                school_id=row.school_id,
                course_id=row.course_id,
                academic_year_id=row.academic_year_id,
                period_id=row.period_id,
                room_id=row.room_id,
                teacher_id=row.teacher_id,
                section_number=row.section_number,
                max_enrollment=row.max_enrollment,
                current_enrollment=row.current_enrollment,
                is_active=row.is_active,
                created_at=row.created_at,
                updated_at=row.updated_at,
                course_code=row.course_code,
                course_name=row.course_name,
                period_name=row.period_name,
                room_name=row.room_name,
            )
            for row in rows
        ]

    # ---------------------------------------------------------- #
    # Conflict detection engine
    # ---------------------------------------------------------- #

    @staticmethod
    async def detect_conflicts(
        db: AsyncSession, tenant_id: UUID, academic_year_id: UUID
    ) -> ConflictCheckResult:
        conflicts: List[ScheduleConflict] = []

        sections_result = await db.execute(
            select(
                Section.id,
                Section.period_id,
                Section.teacher_id,
                Section.room_id,
                Section.max_enrollment,
                Section.current_enrollment,
                Course.course_code,
                Course.name.label("course_name"),
                Period.name.label("period_name"),
                Room.name.label("room_name"),
                Room.capacity.label("room_capacity"),
            )
            .join(Course, Course.id == Section.course_id)
            .join(Period, Period.id == Section.period_id)
            .outerjoin(Room, Room.id == Section.room_id)
            .where(
                Section.tenant_id == tenant_id,
                Section.academic_year_id == academic_year_id,
                Section.is_active == True
            )
        )
        sections = sections_result.all()

        # Teacher double-booking
        teacher_periods: dict = {}
        for s in sections:
            if s.teacher_id:
                key = (s.teacher_id, s.period_id)
                if key in teacher_periods:
                    conflicts.append(ScheduleConflict(
                        conflict_type="teacher_double_booked",
                        severity="error",
                        description=(
                            f"Teacher is assigned to multiple sections during {s.period_name}"
                        ),
                        section_id_1=teacher_periods[key],
                        section_id_2=s.id,
                        affected_entity_id=s.teacher_id,
                        period_name=s.period_name,
                        suggestion="Reassign one section to a different period or teacher"
                    ))
                else:
                    teacher_periods[key] = s.id

        # Room double-booking
        room_periods: dict = {}
        for s in sections:
            if s.room_id:
                key = (s.room_id, s.period_id)
                if key in room_periods:
                    conflicts.append(ScheduleConflict(
                        conflict_type="room_double_booked",
                        severity="error",
                        description=(
                            f"Room '{s.room_name}' is assigned to multiple sections during {s.period_name}"
                        ),
                        section_id_1=room_periods[key],
                        section_id_2=s.id,
                        affected_entity_id=s.room_id,
                        affected_entity_name=s.room_name,
                        period_name=s.period_name,
                        suggestion=f"Move one section to a different room during {s.period_name}"
                    ))
                else:
                    room_periods[key] = s.id

        # Room over capacity
        for s in sections:
            if s.room_id and s.room_capacity and s.max_enrollment > s.room_capacity:
                conflicts.append(ScheduleConflict(
                    conflict_type="room_over_capacity",
                    severity="warning",
                    description=(
                        f"Section max enrollment ({s.max_enrollment}) exceeds "
                        f"room capacity ({s.room_capacity}) in '{s.room_name}'"
                    ),
                    section_id_1=s.id,
                    affected_entity_id=s.room_id,
                    affected_entity_name=s.room_name,
                    suggestion=f"Reduce max enrollment to {s.room_capacity} or assign a larger room"
                ))

        return ConflictCheckResult(
            has_conflicts=len(conflicts) > 0,
            conflict_count=len(conflicts),
            conflicts=conflicts
        )

    @staticmethod
    async def _check_new_section_conflicts(
        db: AsyncSession, tenant_id: UUID, payload: SectionCreate
    ) -> List[ScheduleConflict]:
        conflicts = []

        # Teacher conflict
        if payload.teacher_id:
            result = await db.execute(
                select(Section).where(
                    Section.tenant_id == tenant_id,
                    Section.teacher_id == payload.teacher_id,
                    Section.period_id == payload.period_id,
                    Section.academic_year_id == payload.academic_year_id,
                    Section.is_active == True
                )
            )
            if result.scalar_one_or_none():
                conflicts.append(ScheduleConflict(
                    conflict_type="teacher_double_booked",
                    severity="error",
                    description="Teacher already has a section scheduled during this period",
                    affected_entity_id=payload.teacher_id,
                    suggestion="Choose a different period or assign a different teacher"
                ))

        # Room conflict
        if payload.room_id:
            result = await db.execute(
                select(Section).where(
                    Section.tenant_id == tenant_id,
                    Section.room_id == payload.room_id,
                    Section.period_id == payload.period_id,
                    Section.academic_year_id == payload.academic_year_id,
                    Section.is_active == True
                )
            )
            if result.scalar_one_or_none():
                conflicts.append(ScheduleConflict(
                    conflict_type="room_double_booked",
                    severity="error",
                    description="Room is already assigned to another section during this period",
                    affected_entity_id=payload.room_id,
                    suggestion="Choose a different period or assign a different room"
                ))

        return conflicts

    @staticmethod
    async def _check_student_period_conflict(
        db: AsyncSession, tenant_id: UUID, student_id: UUID, new_section: Section
    ) -> List[ScheduleConflict]:
        conflicts = []
        result = await db.execute(
            select(Section.id, Course.name.label("course_name"), Period.name.label("period_name"))
            .join(StudentSection, StudentSection.section_id == Section.id)
            .join(Course, Course.id == Section.course_id)
            .join(Period, Period.id == Section.period_id)
            .where(
                StudentSection.tenant_id == tenant_id,
                StudentSection.student_id == student_id,
                StudentSection.status == "active",
                Section.period_id == new_section.period_id,
                Section.academic_year_id == new_section.academic_year_id
            )
        )
        existing = result.first()
        if existing:
            conflicts.append(ScheduleConflict(
                conflict_type="student_double_booked",
                severity="error",
                description=(
                    f"Student already enrolled in '{existing.course_name}' "
                    f"during {existing.period_name}"
                ),
                affected_entity_id=student_id,
                period_name=existing.period_name,
                suggestion="Drop the existing section or choose a different period"
            ))
        return conflicts