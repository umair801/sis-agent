"""
C3 -- Conflict Detection Agent
Detects scheduling conflicts and IEP deadline alerts,
then uses Claude to generate resolution suggestions.
"""

import json
from datetime import datetime
from typing import Any, Optional

import anthropic
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger


# ---------------------------------------------------------------------------
# Conflict severity levels
# ---------------------------------------------------------------------------

SEVERITY_CRITICAL = "critical"   # Requires immediate action
SEVERITY_WARNING  = "warning"    # Requires attention soon
SEVERITY_INFO     = "info"       # Informational, no immediate action needed


# ---------------------------------------------------------------------------
# SQL: Scheduling conflict queries
# ---------------------------------------------------------------------------

SQL_TEACHER_CONFLICTS = """
    SELECT
        u.first_name || ' ' || u.last_name AS teacher_name,
        u.id AS teacher_id,
        p.name AS period_name,
        p.id AS period_id,
        ay.name AS academic_year,
        COUNT(sec.id) AS section_count,
        STRING_AGG(c.name || ' (' || sec.section_number || ')', ', ') AS conflicting_sections
    FROM sis_section sec
    JOIN sis_user u       ON u.id = sec.teacher_id
    JOIN sis_period p     ON p.id = sec.period_id
    JOIN sis_course c     ON c.id = sec.course_id
    JOIN sis_academic_year ay ON ay.id = sec.academic_year_id
    WHERE sec.tenant_id = :tenant_id
      AND sec.is_active = TRUE
      AND ay.is_current = TRUE
      AND sec.teacher_id IS NOT NULL
    GROUP BY u.id, u.first_name, u.last_name, p.id, p.name, ay.name
    HAVING COUNT(sec.id) > 1
    ORDER BY section_count DESC, teacher_name
"""

SQL_ROOM_CONFLICTS = """
    SELECT
        r.name AS room_name,
        r.id AS room_id,
        p.name AS period_name,
        p.id AS period_id,
        ay.name AS academic_year,
        COUNT(sec.id) AS section_count,
        STRING_AGG(c.name || ' (' || sec.section_number || ')', ', ') AS conflicting_sections
    FROM sis_section sec
    JOIN sis_room r        ON r.id = sec.room_id
    JOIN sis_period p      ON p.id = sec.period_id
    JOIN sis_course c      ON c.id = sec.course_id
    JOIN sis_academic_year ay ON ay.id = sec.academic_year_id
    WHERE sec.tenant_id = :tenant_id
      AND sec.is_active = TRUE
      AND ay.is_current = TRUE
      AND sec.room_id IS NOT NULL
    GROUP BY r.id, r.name, p.id, p.name, ay.name
    HAVING COUNT(sec.id) > 1
    ORDER BY section_count DESC, room_name
"""

# ---------------------------------------------------------------------------
# SQL: IEP deadline queries
# ---------------------------------------------------------------------------

SQL_IEP_OVERDUE = """
    SELECT
        s.first_name || ' ' || s.last_name AS student_name,
        s.student_number,
        s.id AS student_id,
        i.id AS iep_id,
        i.disability_category,
        i.status AS iep_status,
        i.next_review_date,
        (CURRENT_DATE - i.next_review_date) AS days_overdue,
        i.end_date
    FROM sis_iep i
    JOIN sis_student s ON s.id = i.student_id
    WHERE i.tenant_id = :tenant_id
      AND i.status IN ('active', 'draft')
      AND i.next_review_date < CURRENT_DATE
    ORDER BY i.next_review_date ASC
    LIMIT 100
"""

SQL_IEP_DUE_SOON = """
    SELECT
        s.first_name || ' ' || s.last_name AS student_name,
        s.student_number,
        s.id AS student_id,
        i.id AS iep_id,
        i.disability_category,
        i.status AS iep_status,
        i.next_review_date,
        (i.next_review_date - CURRENT_DATE) AS days_until_review,
        i.end_date
    FROM sis_iep i
    JOIN sis_student s ON s.id = i.student_id
    WHERE i.tenant_id = :tenant_id
      AND i.status IN ('active', 'draft')
      AND i.next_review_date >= CURRENT_DATE
      AND i.next_review_date <= CURRENT_DATE + INTERVAL '30 days'
    ORDER BY i.next_review_date ASC
    LIMIT 100
"""

SQL_IEP_EXPIRING = """
    SELECT
        s.first_name || ' ' || s.last_name AS student_name,
        s.student_number,
        s.id AS student_id,
        i.id AS iep_id,
        i.disability_category,
        i.status AS iep_status,
        i.end_date,
        (i.end_date - CURRENT_DATE) AS days_until_expiry
    FROM sis_iep i
    JOIN sis_student s ON s.id = i.student_id
    WHERE i.tenant_id = :tenant_id
      AND i.status = 'active'
      AND i.end_date <= CURRENT_DATE + INTERVAL '60 days'
      AND i.end_date >= CURRENT_DATE
    ORDER BY i.end_date ASC
    LIMIT 100
"""


# ---------------------------------------------------------------------------
# Claude suggestion generator
# ---------------------------------------------------------------------------

async def _generate_suggestions(
    client: anthropic.AsyncAnthropic,
    conflict_type: str,
    conflicts: list[dict],
) -> str:
    if not conflicts:
        return "No conflicts detected. No action required."

    sample = json.dumps(conflicts[:10], default=str)

    prompt = (
        f"You are an expert school administrator assistant.\n"
        f"Conflict type: {conflict_type}\n"
        f"Conflicts found ({len(conflicts)} total, showing up to 10):\n{sample}\n\n"
        f"Provide 3-5 specific, actionable resolution steps for these conflicts. "
        f"Be concise and practical. Use numbered steps. Do not use em-dashes."
    )

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


# ---------------------------------------------------------------------------
# Individual detectors
# ---------------------------------------------------------------------------

async def _detect_teacher_conflicts(
    db: AsyncSession, tenant_id: str
) -> list[dict]:
    result = await db.execute(text(SQL_TEACHER_CONFLICTS), {"tenant_id": tenant_id})
    cols = list(result.keys())
    return [dict(zip(cols, row)) for row in result.fetchall()]


async def _detect_room_conflicts(
    db: AsyncSession, tenant_id: str
) -> list[dict]:
    result = await db.execute(text(SQL_ROOM_CONFLICTS), {"tenant_id": tenant_id})
    cols = list(result.keys())
    return [dict(zip(cols, row)) for row in result.fetchall()]


async def _detect_iep_overdue(
    db: AsyncSession, tenant_id: str
) -> list[dict]:
    result = await db.execute(text(SQL_IEP_OVERDUE), {"tenant_id": tenant_id})
    cols = list(result.keys())
    return [dict(zip(cols, row)) for row in result.fetchall()]


async def _detect_iep_due_soon(
    db: AsyncSession, tenant_id: str
) -> list[dict]:
    result = await db.execute(text(SQL_IEP_DUE_SOON), {"tenant_id": tenant_id})
    cols = list(result.keys())
    return [dict(zip(cols, row)) for row in result.fetchall()]


async def _detect_iep_expiring(
    db: AsyncSession, tenant_id: str
) -> list[dict]:
    result = await db.execute(text(SQL_IEP_EXPIRING), {"tenant_id": tenant_id})
    cols = list(result.keys())
    return [dict(zip(cols, row)) for row in result.fetchall()]


# ---------------------------------------------------------------------------
# Main conflict detection runner
# ---------------------------------------------------------------------------

async def run_conflict_detection(
    tenant_id: str,
    db: AsyncSession,
    check_scheduling: bool = True,
    check_iep: bool = True,
) -> dict[str, Any]:
    """
    Run all conflict detectors and return structured findings with
    Claude-generated resolution suggestions per conflict category.
    """
    started_at = datetime.utcnow()
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    findings = []
    total_critical = 0
    total_warning = 0

    # --- Scheduling conflicts ---
    if check_scheduling:
        teacher_conflicts = await _detect_teacher_conflicts(db, tenant_id)
        room_conflicts    = await _detect_room_conflicts(db, tenant_id)

        if teacher_conflicts:
            suggestions = await _generate_suggestions(
                client, "Teacher double-booked in same period", teacher_conflicts
            )
            findings.append({
                "category": "scheduling",
                "type": "teacher_conflict",
                "severity": SEVERITY_CRITICAL,
                "count": len(teacher_conflicts),
                "title": "Teacher Scheduling Conflicts",
                "description": f"{len(teacher_conflicts)} teacher(s) assigned to multiple sections in the same period.",
                "items": teacher_conflicts,
                "suggestions": suggestions,
            })
            total_critical += len(teacher_conflicts)
        else:
            findings.append({
                "category": "scheduling",
                "type": "teacher_conflict",
                "severity": SEVERITY_INFO,
                "count": 0,
                "title": "Teacher Scheduling Conflicts",
                "description": "No teacher scheduling conflicts detected.",
                "items": [],
                "suggestions": "No action required.",
            })

        if room_conflicts:
            suggestions = await _generate_suggestions(
                client, "Room double-booked in same period", room_conflicts
            )
            findings.append({
                "category": "scheduling",
                "type": "room_conflict",
                "severity": SEVERITY_CRITICAL,
                "count": len(room_conflicts),
                "title": "Room Scheduling Conflicts",
                "description": f"{len(room_conflicts)} room(s) assigned to multiple sections in the same period.",
                "items": room_conflicts,
                "suggestions": suggestions,
            })
            total_critical += len(room_conflicts)
        else:
            findings.append({
                "category": "scheduling",
                "type": "room_conflict",
                "severity": SEVERITY_INFO,
                "count": 0,
                "title": "Room Scheduling Conflicts",
                "description": "No room scheduling conflicts detected.",
                "items": [],
                "suggestions": "No action required.",
            })

    # --- IEP deadline alerts ---
    if check_iep:
        overdue  = await _detect_iep_overdue(db, tenant_id)
        due_soon = await _detect_iep_due_soon(db, tenant_id)
        expiring = await _detect_iep_expiring(db, tenant_id)

        if overdue:
            suggestions = await _generate_suggestions(
                client, "IEP reviews are overdue (IDEA compliance violation risk)", overdue
            )
            findings.append({
                "category": "iep",
                "type": "iep_overdue",
                "severity": SEVERITY_CRITICAL,
                "count": len(overdue),
                "title": "Overdue IEP Reviews",
                "description": f"{len(overdue)} student(s) have overdue IEP reviews. Immediate action required for IDEA compliance.",
                "items": overdue,
                "suggestions": suggestions,
            })
            total_critical += len(overdue)
        else:
            findings.append({
                "category": "iep",
                "type": "iep_overdue",
                "severity": SEVERITY_INFO,
                "count": 0,
                "title": "Overdue IEP Reviews",
                "description": "No overdue IEP reviews. Compliance is current.",
                "items": [],
                "suggestions": "No action required.",
            })

        if due_soon:
            suggestions = await _generate_suggestions(
                client, "IEP reviews due within 30 days", due_soon
            )
            findings.append({
                "category": "iep",
                "type": "iep_due_soon",
                "severity": SEVERITY_WARNING,
                "count": len(due_soon),
                "title": "IEP Reviews Due Within 30 Days",
                "description": f"{len(due_soon)} IEP review(s) due within the next 30 days.",
                "items": due_soon,
                "suggestions": suggestions,
            })
            total_warning += len(due_soon)
        else:
            findings.append({
                "category": "iep",
                "type": "iep_due_soon",
                "severity": SEVERITY_INFO,
                "count": 0,
                "title": "IEP Reviews Due Within 30 Days",
                "description": "No IEP reviews due within the next 30 days.",
                "items": [],
                "suggestions": "No action required.",
            })

        if expiring:
            suggestions = await _generate_suggestions(
                client, "IEP plans expiring within 60 days", expiring
            )
            findings.append({
                "category": "iep",
                "type": "iep_expiring",
                "severity": SEVERITY_WARNING,
                "count": len(expiring),
                "title": "IEP Plans Expiring Within 60 Days",
                "description": f"{len(expiring)} IEP plan(s) expiring within 60 days. Renewal required.",
                "items": expiring,
                "suggestions": suggestions,
            })
            total_warning += len(expiring)
        else:
            findings.append({
                "category": "iep",
                "type": "iep_expiring",
                "severity": SEVERITY_INFO,
                "count": 0,
                "title": "IEP Plans Expiring Within 60 Days",
                "description": "No IEP plans expiring within 60 days.",
                "items": [],
                "suggestions": "No action required.",
            })

    duration_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)

    overall_status = (
        "critical" if total_critical > 0
        else "warning" if total_warning > 0
        else "clear"
    )

    logger.info(
        f"Conflict detection complete | tenant={tenant_id} "
        f"critical={total_critical} warning={total_warning} ms={duration_ms}"
    )

    return {
        "success": True,
        "tenant_id": tenant_id,
        "scanned_at": datetime.utcnow().isoformat(),
        "overall_status": overall_status,
        "total_critical": total_critical,
        "total_warning": total_warning,
        "findings": findings,
        "duration_ms": duration_ms,
    }