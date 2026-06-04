"""
C2 -- Automated Report Generator API Routes
GET  /api/v1/reports/types         -- list available report types
POST /api/v1/reports/generate      -- generate a report
"""

from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.services.report_service import generate_report, ReportType

router = APIRouter(prefix="/reports", tags=["Reports"])


class ReportRequest(BaseModel):
    report_type: str
    school_id: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


@router.get(
    "/types",
    summary="List available report types",
)
async def list_report_types():
    return {
        "report_types": [rt.value for rt in ReportType],
        "descriptions": {
            "attendance_weekly":   "Weekly attendance summary with at-risk student flags",
            "attendance_monthly":  "Monthly attendance with chronic absenteeism analysis",
            "grade_distribution":  "Grade distribution by course with failure rate analysis",
            "student_gpa_summary": "Student GPA rankings with at-risk identification",
            "iep_compliance":      "IEP review deadlines and compliance status",
            "enrollment_summary":  "Current enrollment counts by grade level",
        },
    }


@router.post(
    "/generate",
    summary="Generate an automated report with AI narrative",
)
async def generate_report_endpoint(
    payload: ReportRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant_id: str = str(current_user.tenant_id)

    result = await generate_report(
        report_type=payload.report_type,
        tenant_id=tenant_id,
        db=db,
        school_id=payload.school_id,
        date_from=payload.date_from,
        date_to=payload.date_to,
    )
    return result