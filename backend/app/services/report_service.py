"""
C2 -- Automated Report Generator
Generates structured attendance, grades, and compliance reports
using live DB data + Claude AI narrative summaries.
"""

import json
from datetime import date, datetime, timedelta
from typing import Any, Optional
from enum import Enum

import anthropic
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger


# ---------------------------------------------------------------------------
# Report types
# ---------------------------------------------------------------------------

class ReportType(str, Enum):
    ATTENDANCE_WEEKLY    = "attendance_weekly"
    ATTENDANCE_MONTHLY   = "attendance_monthly"
    GRADE_DISTRIBUTION   = "grade_distribution"
    STUDENT_GPA_SUMMARY  = "student_gpa_summary"
    IEP_COMPLIANCE       = "iep_compliance"
    ENROLLMENT_SUMMARY   = "enrollment_summary"


# ---------------------------------------------------------------------------
# SQL queries per report type
# ---------------------------------------------------------------------------

REPORT_QUERIES: dict[str, str] = {

    ReportType.ATTENDANCE_WEEKLY: """
        SELECT
            s.first_name || ' ' || s.last_name AS student_name,
            s.student_number,
            COUNT(*) FILTER (WHERE ad.status = 'absent')  AS absences,
            COUNT(*) FILTER (WHERE ad.status = 'tardy')   AS tardies,
            COUNT(*) FILTER (WHERE ad.status = 'excused') AS excused,
            COUNT(*) FILTER (WHERE ad.status = 'present') AS present,
            COUNT(*) AS total_records
        FROM sis_attendance_daily ad
        JOIN sis_student s ON s.id = ad.student_id
        WHERE ad.tenant_id = :tenant_id
          AND ad.attendance_date >= CURRENT_DATE - INTERVAL '7 days'
          AND ad.attendance_date < CURRENT_DATE
        GROUP BY s.id, s.first_name, s.last_name, s.student_number
        ORDER BY absences DESC, s.last_name
        LIMIT 100
    """,

    ReportType.ATTENDANCE_MONTHLY: """
        SELECT
            s.first_name || ' ' || s.last_name AS student_name,
            s.student_number,
            COUNT(*) FILTER (WHERE ad.status = 'absent')  AS absences,
            COUNT(*) FILTER (WHERE ad.status = 'tardy')   AS tardies,
            COUNT(*) FILTER (WHERE ad.status = 'excused') AS excused,
            COUNT(*) FILTER (WHERE ad.status = 'present') AS present,
            COUNT(*) AS total_records,
            ROUND(
                COUNT(*) FILTER (WHERE ad.status = 'present')::NUMERIC
                / NULLIF(COUNT(*), 0) * 100, 1
            ) AS attendance_rate_pct
        FROM sis_attendance_daily ad
        JOIN sis_student s ON s.id = ad.student_id
        WHERE ad.tenant_id = :tenant_id
          AND ad.attendance_date >= DATE_TRUNC('month', CURRENT_DATE)
          AND ad.attendance_date < CURRENT_DATE
        GROUP BY s.id, s.first_name, s.last_name, s.student_number
        ORDER BY attendance_rate_pct ASC NULLS LAST
        LIMIT 200
    """,

    ReportType.GRADE_DISTRIBUTION: """
        SELECT
            c.name AS course_name,
            c.course_code AS course_code,
            COUNT(g.id) AS total_grades,
            COUNT(*) FILTER (WHERE g.letter_grade IN ('A+','A','A-')) AS count_a,
            COUNT(*) FILTER (WHERE g.letter_grade IN ('B+','B','B-')) AS count_b,
            COUNT(*) FILTER (WHERE g.letter_grade IN ('C+','C','C-')) AS count_c,
            COUNT(*) FILTER (WHERE g.letter_grade IN ('D+','D','D-')) AS count_d,
            COUNT(*) FILTER (WHERE g.letter_grade = 'F')              AS count_f,
            ROUND(AVG(g.percentage), 2) AS avg_score
        FROM sis_grade g
        JOIN sis_section sec ON sec.id = g.section_id
        JOIN sis_course c    ON c.id = sec.course_id
        WHERE g.tenant_id = :tenant_id
        GROUP BY c.id, c.name, c.course_code
        ORDER BY c.name
    """,

    ReportType.STUDENT_GPA_SUMMARY: """
        SELECT
            s.first_name || ' ' || s.last_name AS student_name,
            s.student_number,
            gl.name AS grade_level,
            ROUND(AVG(g.percentage), 2) AS avg_score,
            COUNT(g.id) AS total_assignments
        FROM sis_grade g
        JOIN sis_student s      ON s.id = g.student_id
        JOIN sis_enrollment e   ON e.student_id = s.id AND e.tenant_id = :tenant_id
        JOIN sis_grade_level gl ON gl.id = e.grade_level_id
        WHERE g.tenant_id = :tenant_id
          AND e.status = 'active'
        GROUP BY s.id, s.first_name, s.last_name, s.student_number, gl.name
        ORDER BY avg_score DESC NULLS LAST
        LIMIT 200
    """,

    ReportType.IEP_COMPLIANCE: """
        SELECT
            s.first_name || ' ' || s.last_name AS student_name,
            s.student_number,
            i.disability_category,
            i.status AS iep_status,
            i.start_date,
            i.end_date,
            i.next_review_date,
            CASE
                WHEN i.next_review_date < CURRENT_DATE THEN 'OVERDUE'
                WHEN i.next_review_date <= CURRENT_DATE + INTERVAL '30 days' THEN 'DUE_SOON'
                ELSE 'OK'
            END AS compliance_flag,
            (i.next_review_date - CURRENT_DATE) AS days_until_review
        FROM sis_iep i
        JOIN sis_student s ON s.id = i.student_id
        WHERE i.tenant_id = :tenant_id
          AND i.status IN ('active', 'draft')
        ORDER BY i.next_review_date ASC
        LIMIT 200
    """,

    ReportType.ENROLLMENT_SUMMARY: """
        SELECT
            gl.name AS grade_level,
            gl.sort_order,
            COUNT(e.id) AS enrolled_students,
            COUNT(*) FILTER (WHERE e.status = 'active')    AS active,
            COUNT(*) FILTER (WHERE e.status = 'withdrawn') AS withdrawn,
            COUNT(*) FILTER (WHERE e.status = 'graduated') AS graduated
        FROM sis_enrollment e
        JOIN sis_grade_level gl ON gl.id = e.grade_level_id
        JOIN sis_academic_year ay ON ay.id = e.academic_year_id
        WHERE e.tenant_id = :tenant_id
          AND ay.is_current = TRUE
        GROUP BY gl.id, gl.name, gl.sort_order
        ORDER BY gl.sort_order
    """,
}

# ---------------------------------------------------------------------------
# Narrative prompts per report type
# ---------------------------------------------------------------------------

NARRATIVE_PROMPTS: dict[str, str] = {
    ReportType.ATTENDANCE_WEEKLY: (
        "Write a concise weekly attendance summary for school administrators. "
        "Highlight students with 2+ absences, overall attendance trends, and any concerns. "
        "Keep it to 3-5 sentences. Do not use em-dashes."
    ),
    ReportType.ATTENDANCE_MONTHLY: (
        "Write a monthly attendance narrative for district leadership. "
        "Highlight chronic absenteeism (attendance rate below 90%), overall trends, "
        "and recommended interventions. 3-5 sentences. No em-dashes."
    ),
    ReportType.GRADE_DISTRIBUTION: (
        "Write a grade distribution summary for the principal. "
        "Identify courses with high failure rates (F count > 10% of total), "
        "strong performers, and overall academic health. 3-5 sentences. No em-dashes."
    ),
    ReportType.STUDENT_GPA_SUMMARY: (
        "Write a GPA summary narrative for academic counselors. "
        "Highlight top performers, students at risk (avg score below 65), "
        "and grade-level trends. 3-5 sentences. No em-dashes."
    ),
    ReportType.IEP_COMPLIANCE: (
        "Write an IEP compliance status report for the SpEd coordinator. "
        "Flag any OVERDUE reviews, count DUE_SOON items, and summarize overall compliance. "
        "Include urgency language for overdue items. 3-5 sentences. No em-dashes."
    ),
    ReportType.ENROLLMENT_SUMMARY: (
        "Write an enrollment summary for district administration. "
        "Summarize total enrollment, grade-level distribution, and any notable patterns. "
        "3-5 sentences. No em-dashes."
    ),
}

# ---------------------------------------------------------------------------
# Report metadata
# ---------------------------------------------------------------------------

REPORT_METADATA: dict[str, dict] = {
    ReportType.ATTENDANCE_WEEKLY:   {"title": "Weekly Attendance Report",        "category": "attendance"},
    ReportType.ATTENDANCE_MONTHLY:  {"title": "Monthly Attendance Report",       "category": "attendance"},
    ReportType.GRADE_DISTRIBUTION:  {"title": "Grade Distribution Report",       "category": "grades"},
    ReportType.STUDENT_GPA_SUMMARY: {"title": "Student GPA Summary",             "category": "grades"},
    ReportType.IEP_COMPLIANCE:      {"title": "IEP Compliance Status Report",    "category": "compliance"},
    ReportType.ENROLLMENT_SUMMARY:  {"title": "Enrollment Summary Report",       "category": "enrollment"},
}


# ---------------------------------------------------------------------------
# Main report generator
# ---------------------------------------------------------------------------

async def generate_report(
    report_type: str,
    tenant_id: str,
    db: AsyncSession,
    school_id: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> dict[str, Any]:
    """
    Generate a structured report with live data and AI narrative.
    Returns a dict with: title, category, generated_at, row_count, data, narrative, summary_stats.
    """
    if report_type not in REPORT_QUERIES:
        return {
            "success": False,
            "error": f"Unknown report type: {report_type}. Valid types: {list(REPORT_QUERIES.keys())}",
        }

    started_at = datetime.utcnow()
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    meta = REPORT_METADATA[report_type]

    # Step 1: Execute query
    try:
        bind: dict[str, Any] = {"tenant_id": tenant_id}
        result = await db.execute(text(REPORT_QUERIES[report_type]), bind)
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
        row_count = len(rows)
    except Exception as exc:
        logger.error(f"Report query failed: report_type={report_type} error={exc}")
        return {
            "success": False,
            "report_type": report_type,
            "error": str(exc),
        }

    # Step 2: Compute summary stats
    summary_stats = _compute_summary_stats(report_type, rows)

    # Step 3: Generate AI narrative
    narrative = await _generate_narrative(client, report_type, rows, summary_stats)

    duration_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)

    logger.info(
        f"Report generated | type={report_type} tenant={tenant_id} "
        f"rows={row_count} ms={duration_ms}"
    )

    return {
        "success": True,
        "report_type": report_type,
        "title": meta["title"],
        "category": meta["category"],
        "generated_at": datetime.utcnow().isoformat(),
        "tenant_id": tenant_id,
        "row_count": row_count,
        "summary_stats": summary_stats,
        "narrative": narrative,
        "data": rows,
        "duration_ms": duration_ms,
    }


# ---------------------------------------------------------------------------
# Summary stats per report type
# ---------------------------------------------------------------------------

def _compute_summary_stats(report_type: str, rows: list[dict]) -> dict:
    if not rows:
        return {"total_records": 0}

    if report_type == ReportType.ATTENDANCE_WEEKLY:
        total_absences = sum(r.get("absences") or 0 for r in rows)
        total_tardies  = sum(r.get("tardies") or 0 for r in rows)
        at_risk        = [r["student_name"] for r in rows if (r.get("absences") or 0) >= 2]
        return {
            "total_students": len(rows),
            "total_absences": total_absences,
            "total_tardies": total_tardies,
            "students_at_risk": at_risk,
            "at_risk_count": len(at_risk),
        }

    if report_type == ReportType.ATTENDANCE_MONTHLY:
        chronic = [r["student_name"] for r in rows if (r.get("attendance_rate_pct") or 100) < 90]
        rates   = [float(r["attendance_rate_pct"]) for r in rows if r.get("attendance_rate_pct") is not None]
        return {
            "total_students": len(rows),
            "avg_attendance_rate": round(sum(rates) / len(rates), 1) if rates else None,
            "chronic_absentee_count": len(chronic),
            "chronic_absentees": chronic[:20],
        }

    if report_type == ReportType.GRADE_DISTRIBUTION:
        total_f = sum(r.get("count_f") or 0 for r in rows)
        total_grades = sum(r.get("total_grades") or 0 for r in rows)
        return {
            "total_courses": len(rows),
            "total_grade_entries": total_grades,
            "total_failing": total_f,
            "failure_rate_pct": round(total_f / total_grades * 100, 1) if total_grades else 0,
        }

    if report_type == ReportType.STUDENT_GPA_SUMMARY:
        scores = [float(r["avg_score"]) for r in rows if r.get("avg_score") is not None]
        at_risk = [r["student_name"] for r in rows if (r.get("avg_score") or 100) < 65]
        return {
            "total_students": len(rows),
            "school_avg_score": round(sum(scores) / len(scores), 2) if scores else None,
            "at_risk_count": len(at_risk),
            "at_risk_students": at_risk[:20],
        }

    if report_type == ReportType.IEP_COMPLIANCE:
        overdue   = [r["student_name"] for r in rows if r.get("compliance_flag") == "OVERDUE"]
        due_soon  = [r["student_name"] for r in rows if r.get("compliance_flag") == "DUE_SOON"]
        return {
            "total_active_ieps": len(rows),
            "overdue_count": len(overdue),
            "due_soon_count": len(due_soon),
            "overdue_students": overdue,
            "due_soon_students": due_soon,
        }

    if report_type == ReportType.ENROLLMENT_SUMMARY:
        total = sum(r.get("enrolled_students") or 0 for r in rows)
        active = sum(r.get("active") or 0 for r in rows)
        return {
            "total_enrolled": total,
            "total_active": active,
            "grade_levels": len(rows),
        }

    return {"total_records": len(rows)}


# ---------------------------------------------------------------------------
# AI narrative generator
# ---------------------------------------------------------------------------

async def _generate_narrative(
    client: anthropic.AsyncAnthropic,
    report_type: str,
    rows: list[dict],
    summary_stats: dict,
) -> str:
    if not rows:
        return "No data was found for this report period."

    prompt = NARRATIVE_PROMPTS.get(report_type, "Summarize the report data.")
    sample = json.dumps(rows[:30], default=str)
    stats  = json.dumps(summary_stats, default=str)

    msg = (
        f"Report type: {report_type}\n"
        f"Summary statistics: {stats}\n"
        f"Data sample (up to 30 rows): {sample}\n\n"
        f"Task: {prompt}"
    )

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=400,
        messages=[{"role": "user", "content": msg}],
    )
    return response.content[0].text.strip()