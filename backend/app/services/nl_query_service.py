"""
C1 — Natural Language Query Handler
Routes plain-English questions to parameterized SQL queries,
executes them safely, and returns AI-summarized results with citations.
"""

import json
import re
from typing import Any, Optional
from datetime import datetime

import anthropic
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger

# ---------------------------------------------------------------------------
# Allowed query domains — maps intent labels to safe table/column whitelist
# ---------------------------------------------------------------------------

QUERY_DOMAINS = {
    "attendance": {
        "tables": ["sis_attendance_daily", "sis_attendance_period", "sis_student", "sis_school"],
        "description": "attendance records, absences, tardies, present/absent counts",
    },
    "students": {
        "tables": ["sis_student", "sis_enrollment", "sis_grade_level"],
        "description": "student profiles, enrollment status, grade levels",
    },
    "grades": {
        "tables": ["sis_grade", "sis_assignment", "sis_assignment_category", "sis_section_final_grade", "sis_section", "sis_student"],
        "description": "grades, GPA, assignments, final grades by section",
    },
    "scheduling": {
        "tables": ["sis_section", "sis_course", "sis_room", "sis_period", "sis_teacher_assignment"],
        "description": "class sections, room assignments, teacher schedules, conflicts",
    },
    "sped": {
        "tables": ["sis_iep", "sis_iep_goal", "sis_student", "sis_school"],
        "description": "IEP records, special education students, compliance deadlines",
    },
    "budget": {
        "tables": ["sis_budget", "sis_budget_line_item", "sis_budget_transaction", "sis_fiscal_year"],
        "description": "budget allocations, expenditures, resource forecasting",
    },
    "communication": {
        "tables": ["sis_announcement", "sis_notification_log"],
        "description": "announcements, parent notifications, communication logs",
    },
}

# ---------------------------------------------------------------------------
# Intent + SQL generation prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a SQL expert for a Student Information System (SIS) database using PostgreSQL.
Your job is to convert natural language questions into safe, read-only SELECT queries.

RULES:
1. Only generate SELECT statements. Never INSERT, UPDATE, DELETE, DROP, TRUNCATE, or ALTER.
2. Always filter by tenant_id using the placeholder :tenant_id.
3. Use table aliases for readability.
4. Limit results to 200 rows maximum unless the user asks for aggregates.
5. For date ranges, use CURRENT_DATE for relative dates (e.g., "last week" = CURRENT_DATE - INTERVAL '7 days').
6. Return ONLY valid JSON. No markdown, no explanations outside JSON.

AVAILABLE TABLES AND COLUMNS:

sis_student (id, tenant_id, student_number, first_name, middle_name, last_name, date_of_birth, gender, email, is_active, created_at)
  -- NOTE: enrollment_status lives in sis_enrollment, NOT sis_student
sis_enrollment (id, tenant_id, student_id, school_id, academic_year_id, grade_level_id, enrollment_date, withdrawal_date, status)
  -- status values: 'active', 'withdrawn', 'graduated', 'transferred', 'suspended'
sis_grade_level (id, tenant_id, name, short_name, sort_order)
sis_school (id, tenant_id, name, short_name, is_active)
sis_academic_year (id, tenant_id, name, start_date, end_date, is_current)
sis_attendance_daily (id, tenant_id, student_id, school_id, attendance_date, status, excuse_reason, notes, recorded_by, created_at)
  -- status values: 'present', 'absent', 'tardy', 'excused', 'half_day'
sis_attendance_period (id, tenant_id, student_id, school_id, period_id, attendance_date, status, notes, recorded_by)
  -- status values: 'present', 'absent', 'tardy', 'excused'
sis_period (id, tenant_id, school_id, name, short_name, start_time, end_time, sort_order, is_active)
sis_course (id, tenant_id, course_code, name, description, credits, department, is_active)
sis_section (id, tenant_id, school_id, course_id, academic_year_id, period_id, room_id, teacher_id, section_number, is_active)
sis_grade (id, tenant_id, student_id, assignment_id, section_id, points_earned, percentage, letter_grade, is_excused, is_missing, graded_at)
sis_assignment (id, tenant_id, section_id, category_id, name, max_points, due_date, is_published)
sis_section_final_grade (id, tenant_id, student_id, section_id, academic_year_id, final_percentage, letter_grade, gpa_points, credits_earned, is_passing)
sis_iep (id, tenant_id, student_id, status, disability_category, start_date, end_date, next_review_date, eligibility_date, created_at)
  -- status values: 'draft', 'active', 'expired', 'revoked'
sis_iep_goal (id, iep_id, tenant_id, domain, goal_text, status, sequence)
  -- status values: 'not_started', 'in_progress', 'achieved', 'not_achieved', 'discontinued'
sis_budget (id, tenant_id, fiscal_year_id, school_id, name, status, total_allocated, total_spent, total_forecasted)
  -- status values: 'draft', 'approved', 'active', 'closed'
sis_fiscal_year (id, tenant_id, name, start_date, end_date, is_current)
sis_budget_line_item (id, tenant_id, budget_id, category, name, allocated_amount, spent_amount, forecasted_amount)
  -- category values: 'personnel', 'benefits', 'supplies', 'equipment', 'facilities', 'transportation', 'professional_dev', 'technology', 'special_education', 'contracted_services', 'other'
sis_budget_transaction (id, tenant_id, line_item_id, transaction_type, amount, transaction_date, vendor, description)
sis_announcement (id, tenant_id, school_id, title, body, published_at)
sis_notification_log (id, tenant_id, recipient_user_id, channel, status, sent_at)

Respond with this exact JSON structure:
{
  "intent": "<one of: attendance|students|grades|scheduling|sped|budget|communication|unknown>",
  "confidence": <0.0 to 1.0>,
  "sql": "<safe SELECT query with :tenant_id placeholder>",
  "params": {"tenant_id": "__TENANT_ID__"},
  "summary_prompt": "<instruction for summarizing the results in plain English>",
  "error": null
}

If the question cannot be answered with available tables, set sql to null and error to a user-friendly message.
If the question asks for anything destructive, set sql to null and error to "Only read queries are supported."
"""


def _build_user_message(question: str, context: Optional[dict] = None) -> str:
    ctx_str = ""
    if context:
        ctx_str = f"\nContext: {json.dumps(context)}"
    return f"Question: {question}{ctx_str}\n\nGenerate the SQL query and metadata."


# ---------------------------------------------------------------------------
# SQL safety validator (defense in depth)
# ---------------------------------------------------------------------------

FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|GRANT|REVOKE|EXEC|EXECUTE|"
    r"pg_sleep|pg_read_file|COPY|\\\\|--)\b",
    re.IGNORECASE,
)


def _is_safe_sql(sql: str) -> bool:
    if FORBIDDEN_KEYWORDS.search(sql):
        return False
    stripped = sql.strip().upper()
    if not stripped.startswith("SELECT"):
        return False
    if ":tenant_id" not in sql:
        return False
    return True


# ---------------------------------------------------------------------------
# Result summarizer
# ---------------------------------------------------------------------------

async def _summarize_results(
    client: anthropic.AsyncAnthropic,
    question: str,
    rows: list[dict],
    summary_prompt: str,
    row_count: int,
) -> str:
    if row_count == 0:
        return "No records were found matching your query."

    # Truncate rows for summarization context (keep first 50)
    sample = rows[:50]
    sample_json = json.dumps(sample, default=str)

    summarize_msg = (
        f"Original question: {question}\n\n"
        f"Query returned {row_count} record(s). Sample data (up to 50 rows):\n{sample_json}\n\n"
        f"Task: {summary_prompt}\n\n"
        f"Write a clear, concise 2-4 sentence summary for a school administrator. "
        f"Include key numbers. Do not use em-dashes."
    )

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=400,
        messages=[{"role": "user", "content": summarize_msg}],
    )
    return response.content[0].text.strip()


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

async def handle_nl_query(
    question: str,
    tenant_id: str,
    db: AsyncSession,
    user_role: str,
    school_id: Optional[str] = None,
    context: Optional[dict] = None,
) -> dict[str, Any]:
    """
    Full NL-to-SQL pipeline:
    1. Claude parses intent and generates parameterized SQL
    2. Safety validator checks SQL
    3. Execute query with tenant_id bound
    4. Claude summarizes results
    Returns structured response dict.
    """
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    started_at = datetime.utcnow()

    # Step 1: Parse intent and generate SQL
    try:
        parse_response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": _build_user_message(question, context)}
            ],
        )
        raw = parse_response.content[0].text.strip()

        # Strip any accidental markdown fences
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"```$", "", raw).strip()

        parsed = json.loads(raw)
    except (json.JSONDecodeError, Exception) as exc:
        logger.error(f"NL parse failed: {exc}")
        return {
            "success": False,
            "question": question,
            "intent": "unknown",
            "sql": None,
            "row_count": 0,
            "rows": [],
            "summary": "I could not understand that question. Please rephrase it.",
            "error": str(exc),
            "duration_ms": int((datetime.utcnow() - started_at).total_seconds() * 1000),
        }

    # Step 2: Handle unknown / error from Claude
    if parsed.get("error") or not parsed.get("sql"):
        return {
            "success": False,
            "question": question,
            "intent": parsed.get("intent", "unknown"),
            "sql": None,
            "row_count": 0,
            "rows": [],
            "summary": parsed.get("error", "This question could not be answered with available data."),
            "error": parsed.get("error"),
            "duration_ms": int((datetime.utcnow() - started_at).total_seconds() * 1000),
        }

    sql: str = parsed["sql"]
    intent: str = parsed.get("intent", "unknown")
    summary_prompt: str = parsed.get("summary_prompt", "Summarize the results.")
    confidence: float = parsed.get("confidence", 0.0)

    # Step 3: Safety validation
    if not _is_safe_sql(sql):
        logger.warning(f"Unsafe SQL blocked for tenant {tenant_id}: {sql[:200]}")
        return {
            "success": False,
            "question": question,
            "intent": intent,
            "sql": None,
            "row_count": 0,
            "rows": [],
            "summary": "That query type is not permitted.",
            "error": "SQL failed safety validation.",
            "duration_ms": int((datetime.utcnow() - started_at).total_seconds() * 1000),
        }

    # Step 4: Execute query
    try:
        bind_params: dict[str, Any] = {"tenant_id": tenant_id}

        # Optionally inject school_id if SQL references it
        if ":school_id" in sql and school_id:
            bind_params["school_id"] = school_id

        result = await db.execute(text(sql), bind_params)
        column_names = list(result.keys())
        raw_rows = result.fetchall()
        rows = [dict(zip(column_names, row)) for row in raw_rows]
        row_count = len(rows)

    except Exception as exc:
        logger.error(f"SQL execution error: {exc} | SQL: {sql[:300]}")
        return {
            "success": False,
            "question": question,
            "intent": intent,
            "sql": sql,
            "row_count": 0,
            "rows": [],
            "summary": "The query could not be executed. Please try a different question.",
            "error": str(exc),
            "duration_ms": int((datetime.utcnow() - started_at).total_seconds() * 1000),
        }

    # Step 5: Summarize
    summary = await _summarize_results(client, question, rows, summary_prompt, row_count)

    duration_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)

    logger.info(
        f"NL query OK | tenant={tenant_id} intent={intent} "
        f"rows={row_count} confidence={confidence:.2f} ms={duration_ms}"
    )

    return {
        "success": True,
        "question": question,
        "intent": intent,
        "confidence": confidence,
        "sql": sql,
        "row_count": row_count,
        "rows": rows[:100],  # Return max 100 rows to client
        "summary": summary,
        "error": None,
        "duration_ms": duration_ms,
    }