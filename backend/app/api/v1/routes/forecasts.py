"""
C4 -- Scenario Forecasting Agent API Routes
GET  /api/v1/forecasts/types      -- list available forecast types
POST /api/v1/forecasts/run        -- run a forecast scenario
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.services.forecast_service import (
    run_forecast,
    FORECAST_ENROLLMENT,
    FORECAST_BUDGET,
    FORECAST_ATTENDANCE,
)

router = APIRouter(prefix="/forecasts", tags=["Forecasting"])


class ForecastRequest(BaseModel):
    forecast_type: str


@router.get(
    "/types",
    summary="List available forecast types",
)
async def list_forecast_types():
    return {
        "forecast_types": [
            FORECAST_ENROLLMENT,
            FORECAST_BUDGET,
            FORECAST_ATTENDANCE,
        ],
        "descriptions": {
            FORECAST_ENROLLMENT: "Enrollment trend analysis and next-year projection by grade level",
            FORECAST_BUDGET:     "Budget spend rate analysis, at-risk categories, and year-end projection",
            FORECAST_ATTENDANCE: "Weekly attendance trend analysis and chronic absenteeism risk forecast",
        },
    }


@router.post(
    "/run",
    summary="Run a scenario forecast",
    description=(
        "Runs enrollment, budget, or attendance trend forecasting using historical data. "
        "Returns trend analysis, projections, and an AI-generated narrative with recommendations."
    ),
)
async def run_forecast_endpoint(
    payload: ForecastRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant_id: str = str(current_user.tenant_id)
    return await run_forecast(
        forecast_type=payload.forecast_type,
        tenant_id=tenant_id,
        db=db,
    )