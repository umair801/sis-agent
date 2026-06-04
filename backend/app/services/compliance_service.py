"""
C5 -- Compliance Alert Agent
Monitors IDEA and FERPA compliance across IEP records.
Flags violations, generates audit trail entries, and produces
a formal compliance memo via Claude AI.
"""

import json
from datetime import datetime
from typing import Any

import anthropic
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger


# ---------------------------------------------------------------------------
# Compliance rule definitions
# ---------------------------------------------------------------------------

RULES = {
    "IDEA_001": {
        "code": "IDEA_001",
        "regulation": "IDEA 34 CFR 300.324(b)(1)",
        "title": "Annual IEP Review Overdue",
        "description": "IEP must be reviewed at least once per year. Review date has passed.",
        "severity": "critical",
        "action_required": "Schedule emergency IEP meeting immediately.",
    },
    "IDEA_002": {
        "code": "IDEA_002",
        "regulation": "IDEA 34 CFR 300.324(b)(1)",
        "title": "Annual IEP Review Due Within 30 Days",
        "description": "IEP annual review is approaching within 30 days.",
        "severity": "warning",
        "action_required": "Schedule IEP meeting and notify parents at least 10 days in advance.",
    },
    "IDEA_003": {
        "code": "IDEA_003",
        "regulation": "IDEA 34 CFR 300.301",
        "title": "IEP Plan Expiring Within 60 Days",
        "description": "IEP end date is within 60 days. Re-evaluation or renewal required.",
        "severity": "warning",
        "action_required": "Initiate re-evaluation process and schedule eligibility meeting.",
    },
    "IDEA_004": {
        "code": "IDEA_004",
        "regulation": "IDEA 34 CFR 300.321",
        "title": "IEP in Draft Status",
        "description": "IEP has been in draft status and may not be properly implemented.",
        "severity": "warning",
        "action_required": "Review draft IEP, obtain required signatures, and activate.",
    },
    "IDEA_005": {
        "code": "IDEA_005",
        "regulation": "IDEA 34 CFR 300.320(a)(4)",
        "title": "IEP Has No Goals Defined",
        "description": "Active IEP has zero measurable annual goals recorded in the system.",
        "severity": "critical",
        "action_required": "Convene IEP team to define measurable annual goals immediately.",
    },
    "FERPA_001": {
        "code": "FERPA_001",
        "regulation": "FERPA 34 CFR 99.7",
        "title": "Student Record Missing Required Fields",
        "description": "Student record is missing date of birth or other required identifying fields.",
        "severity": "warning",
        "action_required": "Update student record with complete required information.",
    },
}


# ---------------------------------------------------------------------------
# SQL queries per compliance rule
# ---------------------------------------------------------------------------

SQL_IDEA_001 = """
    SELECT
        s.first_name || ' ' || s.last_name AS student_name,
        s.student_number,
        s.id AS student_id,
        i.id AS iep_id,
        i.disability_category,
        i.next_review_date,
        (CURRENT_DATE - i.next_review_date) AS days_overdue,
        i.status AS iep_status,
        i.end_date
    FROM sis_iep i
    JOIN sis_student s ON s.id = i.student_id
    WHERE i.tenant_id = :tenant_id
      AND i.status IN ('active', 'draft')
      AND i.next_review_date < CURRENT_DATE
    ORDER BY i.next_review_date ASC
"""

SQL_IDEA_002 = """
    SELECT
        s.first_name || ' ' || s.last_name AS student_name,
        s.student_number,
        s.id AS student_id,
        i.id AS iep_id,
        i.disability_category,
        i.next_review_date,
        (i.next_review_date - CURRENT_DATE) AS days_remaining,
        i.status AS iep_status
    FROM sis_iep i
    JOIN sis_student s ON s.id = i.student_id
    WHERE i.tenant_id = :tenant_id
      AND i.status IN ('active', 'draft')
      AND i.next_review_date >= CURRENT_DATE
      AND i.next_review_date <= CURRENT_DATE + INTERVAL '30 days'
    ORDER BY i.next_review_date ASC
"""

SQL_IDEA_003 = """
    SELECT
        s.first_name || ' ' || s.last_name AS student_name,
        s.student_number,
        s.id AS student_id,
        i.id AS iep_id,
        i.disability_category,
        i.end_date,
        (i.end_date - CURRENT_DATE) AS days_until_expiry,
        i.status AS iep_status
    FROM sis_iep i
    JOIN sis_student s ON s.id = i.student_id
    WHERE i.tenant_id = :tenant_id
      AND i.status = 'active'
      AND i.end_date <= CURRENT_DATE + INTERVAL '60 days'
      AND i.end_date >= CURRENT_DATE
    ORDER BY i.end_date ASC
"""

SQL_IDEA_004 = """
    SELECT
        s.first_name || ' ' || s.last_name AS student_name,
        s.student_number,
        s.id AS student_id,
        i.id AS iep_id,
        i.disability_category,
        i.start_date,
        i.status AS iep_status,
        (CURRENT_DATE - i.start_date) AS days_in_draft
    FROM sis_iep i
    JOIN sis_student s ON s.id = i.student_id
    WHERE i.tenant_id = :tenant_id
      AND i.status = 'draft'
    ORDER BY i.start_date ASC
"""

SQL_IDEA_005 = """
    SELECT
        s.first_name || ' ' || s.last_name AS student_name,
        s.student_number,
        s.id AS student_id,
        i.id AS iep_id,
        i.disability_category,
        i.status AS iep_status,
        COUNT(ig.id) AS goal_count
    FROM sis_iep i
    JOIN sis_student s ON s.id = i.student_id
    LEFT JOIN sis_iep_goal ig ON ig.iep_id = i.id
    WHERE i.tenant_id = :tenant_id
      AND i.status = 'active'
    GROUP BY s.id, s.first_name, s.last_name, s.student_number,
             i.id, i.disability_category, i.status
    HAVING COUNT(ig.id) = 0
"""

SQL_FERPA_001 = """
    SELECT
        s.first_name || ' ' || s.last_name AS student_name,
        s.student_number,
        s.id AS student_id,
        s.date_of_birth,
        s.email,
        s.is_active
    FROM sis_student s
    WHERE s.tenant_id = :tenant_id
      AND s.is_active = TRUE
      AND (
          s.date_of_birth IS NULL
          OR s.first_name IS NULL
          OR s.last_name IS NULL
      )
    ORDER BY s.last_name
"""

RULE_SQL_MAP = {
    "IDEA_001": SQL_IDEA_001,
    "IDEA_002": SQL_IDEA_002,
    "IDEA_003": SQL_IDEA_003,
    "IDEA_004": SQL_IDEA_004,
    "IDEA_005": SQL_IDEA_005,
    "FERPA_001": SQL_FERPA_001,
}


# ---------------------------------------------------------------------------
# Compliance memo generator
# ---------------------------------------------------------------------------

async def _generate_compliance_memo(
    client: anthropic.AsyncAnthropic,
    alerts: list[dict],
    summary: dict,
    tenant_id: str,
) -> str:
    if not any(a["count"] > 0 for a in alerts):
        return (
            f"COMPLIANCE STATUS MEMO\n"
            f"Date: {datetime.utcnow().strftime('%B %d, %Y')}\n"
            f"Status: FULLY COMPLIANT\n\n"
            f"All IDEA and FERPA compliance checks passed. "
            f"No violations or risks were detected at this time. "
            f"Continue monitoring per district compliance schedule."
        )

    alerts_json = json.dumps(
        [a for a in alerts if a["count"] > 0],
        default=str
    )
    summary_json = json.dumps(summary, default=str)

    prompt = (
        f"You are a special education compliance officer writing a formal memo.\n"
        f"Date: {datetime.utcnow().strftime('%B %d, %Y')}\n\n"
        f"Compliance alerts found:\n{alerts_json}\n\n"
        f"Summary statistics:\n{summary_json}\n\n"
        f"Write a formal compliance status memo (6-10 sentences) addressed to "
        f"the District Special Education Director. "
        f"Include: overall compliance status, specific IDEA/FERPA violations found, "
        f"regulatory citations, required actions with urgency, and consequences of "
        f"non-compliance (federal funding risk, due process). "
        f"Use formal legal memo language. No em-dashes. "
        f"Start with: COMPLIANCE STATUS MEMO"
    )

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


# ---------------------------------------------------------------------------
# Main compliance runner
# ---------------------------------------------------------------------------

async def run_compliance_check(
    tenant_id: str,
    db: AsyncSession,
) -> dict[str, Any]:
    """
    Run all IDEA and FERPA compliance checks.
    Returns structured alerts, summary stats, audit trail entry,
    and a Claude-generated formal compliance memo.
    """
    started_at = datetime.utcnow()
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    alerts = []
    total_critical = 0
    total_warning = 0
    total_violations = 0

    # Run each rule
    for rule_code, rule_def in RULES.items():
        sql = RULE_SQL_MAP[rule_code]
        try:
            result = await db.execute(text(sql), {"tenant_id": tenant_id})
            cols = list(result.keys())
            rows = [dict(zip(cols, row)) for row in result.fetchall()]
            count = len(rows)
        except Exception as exc:
            logger.error(f"Compliance rule {rule_code} failed: {exc}")
            rows = []
            count = 0

        alert = {
            "rule_code": rule_code,
            "regulation": rule_def["regulation"],
            "title": rule_def["title"],
            "description": rule_def["description"],
            "severity": rule_def["severity"],
            "action_required": rule_def["action_required"],
            "count": count,
            "affected_students": rows,
        }
        alerts.append(alert)

        if count > 0:
            total_violations += count
            if rule_def["severity"] == "critical":
                total_critical += count
            else:
                total_warning += count

    # Overall status
    overall_status = (
        "violation" if total_critical > 0
        else "at_risk"  if total_warning > 0
        else "compliant"
    )

    summary = {
        "overall_status": overall_status,
        "total_violations": total_violations,
        "total_critical": total_critical,
        "total_warning": total_warning,
        "rules_checked": len(RULES),
        "rules_triggered": sum(1 for a in alerts if a["count"] > 0),
        "checked_at": started_at.isoformat(),
    }

    # Generate formal compliance memo
    memo = await _generate_compliance_memo(client, alerts, summary, tenant_id)

    # Audit trail entry (logged, not persisted to DB in this step)
    audit_entry = {
        "event": "compliance_check_run",
        "tenant_id": tenant_id,
        "timestamp": started_at.isoformat(),
        "overall_status": overall_status,
        "total_critical": total_critical,
        "total_warning": total_warning,
        "rules_checked": len(RULES),
    }
    logger.info(f"COMPLIANCE AUDIT: {json.dumps(audit_entry)}")

    duration_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)

    return {
        "success": True,
        "overall_status": overall_status,
        "summary": summary,
        "alerts": alerts,
        "compliance_memo": memo,
        "audit_entry": audit_entry,
        "duration_ms": duration_ms,
    }