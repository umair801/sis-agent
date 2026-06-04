"""
Budget API routes for AgAI_30 SIS.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_roles
from app.db.database import get_db
from app.schemas.auth import TokenPayload
from app.schemas.budget import (
    FiscalYearCreate, FiscalYearUpdate, FiscalYearResponse,
    BudgetCreate, BudgetUpdate, BudgetResponse, BudgetSummary, BudgetOverview,
    BudgetLineItemCreate, BudgetLineItemUpdate, BudgetLineItemResponse,
    BudgetTransactionCreate, BudgetTransactionResponse,
    BudgetForecastCreate, BudgetForecastResponse,
)
from app.services.budget_service import (
    FiscalYearService, BudgetService,
    BudgetLineItemService, BudgetTransactionService,
    BudgetForecastService,
)

router = APIRouter(prefix="/budget", tags=["Budget"])

BUDGET_WRITE_ROLES = ["SuperAdmin", "DistrictAdmin"]
BUDGET_READ_ROLES  = ["SuperAdmin", "DistrictAdmin", "Principal"]


# ===========================================================================
# Fiscal Years
# ===========================================================================

@router.post("/fiscal-years", response_model=FiscalYearResponse, status_code=201)
async def create_fiscal_year(
    payload: FiscalYearCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*BUDGET_WRITE_ROLES)),
):
    return await FiscalYearService.create_fiscal_year(
        db, UUID(current_user.tenant_id), payload
    )


@router.get("/fiscal-years", response_model=List[FiscalYearResponse])
async def list_fiscal_years(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*BUDGET_READ_ROLES)),
):
    return await FiscalYearService.list_fiscal_years(db, UUID(current_user.tenant_id))


@router.get("/fiscal-years/current", response_model=FiscalYearResponse)
async def get_current_fiscal_year(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*BUDGET_READ_ROLES)),
):
    fy = await FiscalYearService.get_current_fiscal_year(db, UUID(current_user.tenant_id))
    if not fy:
        raise HTTPException(status_code=404, detail="No current fiscal year set")
    return fy


@router.patch("/fiscal-years/{fy_id}", response_model=FiscalYearResponse)
async def update_fiscal_year(
    fy_id: UUID,
    payload: FiscalYearUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*BUDGET_WRITE_ROLES)),
):
    fy = await FiscalYearService.update_fiscal_year(
        db, UUID(current_user.tenant_id), fy_id, payload
    )
    if not fy:
        raise HTTPException(status_code=404, detail="Fiscal year not found")
    return fy


# ===========================================================================
# Budgets
# ===========================================================================

@router.post("/budgets", response_model=BudgetResponse, status_code=201)
async def create_budget(
    payload: BudgetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*BUDGET_WRITE_ROLES)),
):
    try:
        return await BudgetService.create_budget(
            db, UUID(current_user.tenant_id), payload, UUID(current_user.sub)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/budgets", response_model=dict)
async def list_budgets(
    fiscal_year_id: Optional[UUID] = Query(None),
    school_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*BUDGET_READ_ROLES)),
):
    budgets, total = await BudgetService.list_budgets(
        db, UUID(current_user.tenant_id), fiscal_year_id, school_id, skip, limit
    )
    return {
        "total": total,
        "data": [BudgetSummary.model_validate(b) for b in budgets],
    }


@router.get("/budgets/overview", response_model=BudgetOverview)
async def get_budget_overview(
    fiscal_year_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*BUDGET_READ_ROLES)),
):
    try:
        return await BudgetService.get_budget_overview(
            db, UUID(current_user.tenant_id), fiscal_year_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/budgets/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    budget_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*BUDGET_READ_ROLES)),
):
    budget = await BudgetService.get_budget(
        db, UUID(current_user.tenant_id), budget_id
    )
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget


@router.patch("/budgets/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: UUID,
    payload: BudgetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*BUDGET_WRITE_ROLES)),
):
    budget = await BudgetService.update_budget(
        db, UUID(current_user.tenant_id), budget_id, payload
    )
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget


@router.delete("/budgets/{budget_id}", status_code=204)
async def delete_budget(
    budget_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*BUDGET_WRITE_ROLES)),
):
    try:
        deleted = await BudgetService.delete_budget(
            db, UUID(current_user.tenant_id), budget_id
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not deleted:
        raise HTTPException(status_code=404, detail="Budget not found")


# ===========================================================================
# Line Items
# ===========================================================================

@router.post("/budgets/{budget_id}/line-items", response_model=BudgetLineItemResponse, status_code=201)
async def add_line_item(
    budget_id: UUID,
    payload: BudgetLineItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*BUDGET_WRITE_ROLES)),
):
    return await BudgetLineItemService.add_line_item(
        db, UUID(current_user.tenant_id), budget_id, payload
    )


@router.patch("/line-items/{item_id}", response_model=BudgetLineItemResponse)
async def update_line_item(
    item_id: UUID,
    payload: BudgetLineItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*BUDGET_WRITE_ROLES)),
):
    item = await BudgetLineItemService.update_line_item(
        db, UUID(current_user.tenant_id), item_id, payload
    )
    if not item:
        raise HTTPException(status_code=404, detail="Line item not found")
    return item


@router.delete("/line-items/{item_id}", status_code=204)
async def delete_line_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*BUDGET_WRITE_ROLES)),
):
    deleted = await BudgetLineItemService.delete_line_item(
        db, UUID(current_user.tenant_id), item_id
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Line item not found")


# ===========================================================================
# Transactions
# ===========================================================================

@router.post("/line-items/{item_id}/transactions", response_model=BudgetTransactionResponse, status_code=201)
async def add_transaction(
    item_id: UUID,
    payload: BudgetTransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*BUDGET_WRITE_ROLES)),
):
    try:
        return await BudgetTransactionService.add_transaction(
            db, UUID(current_user.tenant_id), item_id, payload, UUID(current_user.sub)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ===========================================================================
# Forecasts
# ===========================================================================

@router.post("/budgets/{budget_id}/forecasts", response_model=BudgetForecastResponse, status_code=201)
async def create_forecast(
    budget_id: UUID,
    payload: BudgetForecastCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*BUDGET_WRITE_ROLES)),
):
    return await BudgetForecastService.create_forecast(
        db, UUID(current_user.tenant_id), budget_id, payload, UUID(current_user.sub)
    )


@router.post("/budgets/{budget_id}/forecasts/linear", response_model=List[BudgetForecastResponse], status_code=201)
async def generate_linear_forecast(
    budget_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*BUDGET_WRITE_ROLES)),
):
    try:
        return await BudgetForecastService.generate_linear_forecast(
            db, UUID(current_user.tenant_id), budget_id, UUID(current_user.sub)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/budgets/{budget_id}/forecasts", response_model=List[BudgetForecastResponse])
async def list_forecasts(
    budget_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_roles(*BUDGET_READ_ROLES)),
):
    return await BudgetForecastService.list_forecasts(
        db, UUID(current_user.tenant_id), budget_id
    )