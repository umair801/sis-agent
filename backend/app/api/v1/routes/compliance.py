"""
C5 -- Compliance Alert Agent API Routes
GET  /api/v1/compliance/check    -- run full IDEA/FERPA compliance check
GET  /api/v1/compliance/rules    -- list all compliance rules being monitored
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.services.compliance_service import run_compliance_check, RULES

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.get(
    "/check",
    summary="Run full IDEA and FERPA compliance check",
    description=(
        "Checks all active IEPs and student records against IDEA and FERPA requirements. "
        "Returns severity-ranked alerts, affected students, required actions, "
        "and a Claude-generated formal compliance memo."
    ),
)
async def compliance_check(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant_id: str = str(current_user.tenant_id)
    return await run_compliance_check(tenant_id=tenant_id, db=db)


@router.get(
    "/rules",
    summary="List all compliance rules being monitored",
)
async def list_compliance_rules():
    return {
        "total_rules": len(RULES),
        "rules": list(RULES.values()),
    }