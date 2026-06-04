"""
C4 -- Scenario Forecasting Agent
Generates enrollment trend and budget projection forecasts
using historical data + Claude AI narrative and recommendations.
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
# Forecast types
# ---------------------------------------------------------------------------

FORECAST_ENROLLMENT = "enrollment"
FORECAST_BUDGET     = "budget"
FORECAST_ATTENDANCE = "attendance_trend"


# ---------------------------------------------------------------------------
# SQL: Enrollment history (by academic year + grade level)
# ---------------------------------------------------------------------------

SQL_ENROLLMENT_HISTORY = """
    SELECT
        ay.name AS academic_year,
        ay.start_date,
        ay.end_date,
        ay.is_current,
        gl.name AS grade_level,
        gl.sort_order,
        COUNT(e.id) AS enrolled_count,
        COUNT(*) FILTER (WHERE e.status = 'active')    AS active_count,
        COUNT(*) FILTER (WHERE e.status = 'withdrawn') AS withdrawn_count,
        COUNT(*) FILTER (WHERE e.status = 'graduated') AS graduated_count
    FROM sis_enrollment e
    JOIN sis_academic_year ay ON ay.id = e.academic_year_id
    JOIN sis_grade_level gl   ON gl.id = e.grade_level_id
    WHERE e.tenant_id = :tenant_id
    GROUP BY ay.id, ay.name, ay.start_date, ay.end_date, ay.is_current,
             gl.id, gl.name, gl.sort_order
    ORDER BY ay.start_date, gl.sort_order
"""

SQL_ENROLLMENT_TOTALS = """
    SELECT
        ay.name AS academic_year,
        ay.start_date,
        ay.is_current,
        COUNT(e.id) AS total_enrolled,
        COUNT(*) FILTER (WHERE e.status = 'active')    AS active,
        COUNT(*) FILTER (WHERE e.status = 'withdrawn') AS withdrawn,
        COUNT(*) FILTER (WHERE e.status = 'graduated') AS graduated,
        ROUND(
            COUNT(*) FILTER (WHERE e.status = 'withdrawn')::NUMERIC
            / NULLIF(COUNT(e.id), 0) * 100, 1
        ) AS withdrawal_rate_pct
    FROM sis_enrollment e
    JOIN sis_academic_year ay ON ay.id = e.academic_year_id
    WHERE e.tenant_id = :tenant_id
    GROUP BY ay.id, ay.name, ay.start_date, ay.is_current
    ORDER BY ay.start_date
"""


# ---------------------------------------------------------------------------
# SQL: Budget history
# ---------------------------------------------------------------------------

SQL_BUDGET_HISTORY = """
    SELECT
        fy.name AS fiscal_year,
        fy.start_date,
        fy.end_date,
        fy.is_current,
        b.name AS budget_name,
        b.status AS budget_status,
        b.total_allocated,
        b.total_spent,
        b.total_forecasted,
        ROUND(
            b.total_spent / NULLIF(b.total_allocated, 0) * 100, 1
        ) AS spend_rate_pct,
        ROUND(
            (b.total_allocated - b.total_spent) / NULLIF(b.total_allocated, 0) * 100, 1
        ) AS remaining_pct
    FROM sis_budget b
    JOIN sis_fiscal_year fy ON fy.id = b.fiscal_year_id
    WHERE b.tenant_id = :tenant_id
    ORDER BY fy.start_date
"""

SQL_BUDGET_BY_CATEGORY = """
    SELECT
        bli.category,
        SUM(bli.allocated_amount)  AS total_allocated,
        SUM(bli.spent_amount)      AS total_spent,
        SUM(bli.forecasted_amount) AS total_forecasted,
        ROUND(
            SUM(bli.spent_amount) / NULLIF(SUM(bli.allocated_amount), 0) * 100, 1
        ) AS spend_rate_pct
    FROM sis_budget_line_item bli
    JOIN sis_budget b ON b.id = bli.budget_id
    JOIN sis_fiscal_year fy ON fy.id = b.fiscal_year_id
    WHERE bli.tenant_id = :tenant_id
      AND fy.is_current = TRUE
    GROUP BY bli.category
    ORDER BY total_allocated DESC
"""


# ---------------------------------------------------------------------------
# SQL: Attendance trend
# ---------------------------------------------------------------------------

SQL_ATTENDANCE_TREND = """
    SELECT
        DATE_TRUNC('week', ad.attendance_date)::DATE AS week_start,
        COUNT(*) FILTER (WHERE ad.status = 'present') AS present_count,
        COUNT(*) FILTER (WHERE ad.status = 'absent')  AS absent_count,
        COUNT(*) FILTER (WHERE ad.status = 'tardy')   AS tardy_count,
        COUNT(*) FILTER (WHERE ad.status = 'excused') AS excused_count,
        COUNT(*) AS total_records,
        ROUND(
            COUNT(*) FILTER (WHERE ad.status = 'present')::NUMERIC
            / NULLIF(COUNT(*), 0) * 100, 1
        ) AS attendance_rate_pct
    FROM sis_attendance_daily ad
    WHERE ad.tenant_id = :tenant_id
      AND ad.attendance_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY DATE_TRUNC('week', ad.attendance_date)
    ORDER BY week_start
"""


# ---------------------------------------------------------------------------
# Simple linear trend calculator
# ---------------------------------------------------------------------------

def _calculate_trend(values: list[float]) -> dict:
    """
    Calculate simple linear trend from a list of numeric values.
    Returns slope, direction, and projected next value.
    """
    n = len(values)
    if n < 2:
        return {"slope": 0, "direction": "stable", "projected_next": values[0] if values else 0}

    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    numerator   = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    slope = numerator / denominator if denominator != 0 else 0

    direction = "increasing" if slope > 0.5 else "decreasing" if slope < -0.5 else "stable"
    projected_next = round(values[-1] + slope, 1)

    return {
        "slope": round(slope, 2),
        "direction": direction,
        "projected_next": projected_next,
        "data_points": n,
    }


# ---------------------------------------------------------------------------
# Claude narrative generator
# ---------------------------------------------------------------------------

async def _generate_forecast_narrative(
    client: anthropic.AsyncAnthropic,
    forecast_type: str,
    historical_data: dict,
    trend_analysis: dict,
) -> str:
    historical_json = json.dumps(historical_data, default=str)
    trend_json      = json.dumps(trend_analysis, default=str)

    prompts = {
        FORECAST_ENROLLMENT: (
            "You are an expert school district enrollment analyst.\n"
            "Based on the historical enrollment data and trend analysis below, "
            "provide a 4-6 sentence forecast for the next academic year. "
            "Include: projected total enrollment, grade-level trends, "
            "staffing implications, and capacity planning recommendations. "
            "Be specific with numbers where possible. No em-dashes."
        ),
        FORECAST_BUDGET: (
            "You are an expert school district budget analyst.\n"
            "Based on the historical budget data and spend rate analysis below, "
            "provide a 4-6 sentence budget projection and risk assessment. "
            "Include: whether the district is on track, categories at risk of overspend, "
            "projected year-end balance, and financial planning recommendations. "
            "Be specific with numbers where possible. No em-dashes."
        ),
        FORECAST_ATTENDANCE: (
            "You are an expert school attendance analyst.\n"
            "Based on the weekly attendance trend data below, "
            "provide a 4-6 sentence analysis and forward projection. "
            "Include: overall attendance health, trend direction, "
            "chronic absenteeism risk, and recommended interventions. "
            "Be specific with numbers where possible. No em-dashes."
        ),
    }

    prompt = prompts.get(forecast_type, "Analyze the data and provide a forecast.")

    msg = (
        f"Forecast type: {forecast_type}\n\n"
        f"Historical data:\n{historical_json}\n\n"
        f"Trend analysis:\n{trend_json}\n\n"
        f"Task: {prompt}"
    )

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": msg}],
    )
    return response.content[0].text.strip()


# ---------------------------------------------------------------------------
# Individual forecast runners
# ---------------------------------------------------------------------------

async def _forecast_enrollment(
    db: AsyncSession,
    tenant_id: str,
    client: anthropic.AsyncAnthropic,
) -> dict:
    result_totals = await db.execute(text(SQL_ENROLLMENT_TOTALS), {"tenant_id": tenant_id})
    cols = list(result_totals.keys())
    totals = [dict(zip(cols, row)) for row in result_totals.fetchall()]

    result_by_grade = await db.execute(text(SQL_ENROLLMENT_HISTORY), {"tenant_id": tenant_id})
    cols2 = list(result_by_grade.keys())
    by_grade = [dict(zip(cols2, row)) for row in result_by_grade.fetchall()]

    # Trend on total active enrollment across years
    active_counts = [float(r.get("active") or 0) for r in totals]
    trend = _calculate_trend(active_counts)

    # Current year snapshot
    current = next((r for r in totals if r.get("is_current")), totals[-1] if totals else {})

    historical_data = {
        "yearly_totals": totals,
        "current_year": current,
        "by_grade_level": by_grade[:20],
    }

    narrative = await _generate_forecast_narrative(
        client, FORECAST_ENROLLMENT, historical_data, trend
    )

    return {
        "forecast_type": FORECAST_ENROLLMENT,
        "title": "Enrollment Trend Forecast",
        "current_enrollment": current.get("active", 0),
        "trend": trend,
        "projected_next_year": trend["projected_next"],
        "historical_years": len(totals),
        "narrative": narrative,
        "data": {
            "yearly_totals": totals,
            "by_grade": by_grade,
        },
    }


async def _forecast_budget(
    db: AsyncSession,
    tenant_id: str,
    client: anthropic.AsyncAnthropic,
) -> dict:
    result_history = await db.execute(text(SQL_BUDGET_HISTORY), {"tenant_id": tenant_id})
    cols = list(result_history.keys())
    history = [dict(zip(cols, row)) for row in result_history.fetchall()]

    result_categories = await db.execute(text(SQL_BUDGET_BY_CATEGORY), {"tenant_id": tenant_id})
    cols2 = list(result_categories.keys())
    categories = [dict(zip(cols2, row)) for row in result_categories.fetchall()]

    # Trend on spend rate
    spend_rates = [float(r.get("spend_rate_pct") or 0) for r in history]
    trend = _calculate_trend(spend_rates)

    current = next((r for r in history if r.get("is_current")), history[-1] if history else {})

    # Identify at-risk categories (spend rate > 80%)
    at_risk = [
        c for c in categories
        if (c.get("spend_rate_pct") or 0) > 80
    ]

    historical_data = {
        "budget_history": history,
        "current_budget": current,
        "spend_by_category": categories,
        "at_risk_categories": at_risk,
    }

    narrative = await _generate_forecast_narrative(
        client, FORECAST_BUDGET, historical_data, trend
    )

    return {
        "forecast_type": FORECAST_BUDGET,
        "title": "Budget Projection",
        "current_allocated": current.get("total_allocated", 0),
        "current_spent": current.get("total_spent", 0),
        "current_spend_rate_pct": current.get("spend_rate_pct", 0),
        "at_risk_categories": at_risk,
        "trend": trend,
        "narrative": narrative,
        "data": {
            "budget_history": history,
            "spend_by_category": categories,
        },
    }


async def _forecast_attendance(
    db: AsyncSession,
    tenant_id: str,
    client: anthropic.AsyncAnthropic,
) -> dict:
    result = await db.execute(text(SQL_ATTENDANCE_TREND), {"tenant_id": tenant_id})
    cols = list(result.keys())
    weekly = [dict(zip(cols, row)) for row in result.fetchall()]

    rates = [float(r.get("attendance_rate_pct") or 0) for r in weekly]
    trend = _calculate_trend(rates)

    avg_rate = round(sum(rates) / len(rates), 1) if rates else 0
    chronic_risk_weeks = [r for r in weekly if (r.get("attendance_rate_pct") or 100) < 90]

    historical_data = {
        "weekly_trend": weekly,
        "average_rate_90d": avg_rate,
        "weeks_below_90pct": len(chronic_risk_weeks),
        "total_weeks": len(weekly),
    }

    narrative = await _generate_forecast_narrative(
        client, FORECAST_ATTENDANCE, historical_data, trend
    )

    return {
        "forecast_type": FORECAST_ATTENDANCE,
        "title": "Attendance Trend Forecast",
        "average_attendance_rate": avg_rate,
        "trend": trend,
        "weeks_analyzed": len(weekly),
        "chronic_risk_weeks": len(chronic_risk_weeks),
        "narrative": narrative,
        "data": {"weekly_trend": weekly},
    }


# ---------------------------------------------------------------------------
# Main forecast runner
# ---------------------------------------------------------------------------

async def run_forecast(
    forecast_type: str,
    tenant_id: str,
    db: AsyncSession,
) -> dict[str, Any]:
    """
    Run a specific forecast scenario and return structured results
    with trend analysis and Claude AI narrative.
    """
    started_at = datetime.utcnow()
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    valid_types = [FORECAST_ENROLLMENT, FORECAST_BUDGET, FORECAST_ATTENDANCE]
    if forecast_type not in valid_types:
        return {
            "success": False,
            "error": f"Unknown forecast type: {forecast_type}. Valid: {valid_types}",
        }

    try:
        if forecast_type == FORECAST_ENROLLMENT:
            result = await _forecast_enrollment(db, tenant_id, client)
        elif forecast_type == FORECAST_BUDGET:
            result = await _forecast_budget(db, tenant_id, client)
        else:
            result = await _forecast_attendance(db, tenant_id, client)

    except Exception as exc:
        logger.error(f"Forecast failed: type={forecast_type} error={exc}")
        return {
            "success": False,
            "forecast_type": forecast_type,
            "error": str(exc),
        }

    duration_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)

    logger.info(
        f"Forecast complete | type={forecast_type} tenant={tenant_id} ms={duration_ms}"
    )

    return {
        "success": True,
        "generated_at": datetime.utcnow().isoformat(),
        "duration_ms": duration_ms,
        **result,
    }