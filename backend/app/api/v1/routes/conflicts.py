"""
C3 -- Conflict Detection Agent API Routes
POST /api/v1/conflicts/scan   -- run full conflict detection
GET  /api/v1/conflicts/scan   -- same, no body needed
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.services.conflict_service import run_conflict_detection

router = APIRouter(prefix="/conflicts", tags=["Conflict Detection"])


class ConflictScanRequest(BaseModel):
    check_scheduling: bool = True
    check_iep: bool = True


@router.post(
    "/scan",
    summary="Run conflict detection scan",
    description=(
        "Scans for scheduling conflicts (teacher/room double-booking) and "
        "IEP deadline alerts (overdue, due soon, expiring). "
        "Returns structured findings with severity levels and AI-generated resolution suggestions."
    ),
)
async def scan_conflicts(
    payload: ConflictScanRequest = ConflictScanRequest(),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant_id: str = str(current_user.tenant_id)

    return await run_conflict_detection(
        tenant_id=tenant_id,
        db=db,
        check_scheduling=payload.check_scheduling,
        check_iep=payload.check_iep,
    )


@router.get(
    "/scan",
    summary="Run conflict detection scan (GET)",
)
async def scan_conflicts_get(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant_id: str = str(current_user.tenant_id)
    return await run_conflict_detection(
        tenant_id=tenant_id,
        db=db,
    )