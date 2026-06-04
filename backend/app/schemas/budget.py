"""
Pydantic schemas for Budget module.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.budget import (
    BudgetStatus, BudgetCategory, TransactionType, ForecastMethod
)


# ===========================================================================
# FiscalYear
# ===========================================================================

class FiscalYearCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    is_current: bool = False


class FiscalYearUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None


class FiscalYearResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    start_date: date
    end_date: date
    is_current: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ===========================================================================
# BudgetTransaction
# ===========================================================================

class BudgetTransactionCreate(BaseModel):
    transaction_type: TransactionType = TransactionType.EXPENSE
    amount: Decimal = Field(..., gt=0)
    transaction_date: date
    vendor: Optional[str] = None
    description: Optional[str] = None
    reference_number: Optional[str] = None


class BudgetTransactionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    line_item_id: UUID
    transaction_type: TransactionType
    amount: Decimal
    transaction_date: date
    vendor: Optional[str] = None
    description: Optional[str] = None
    reference_number: Optional[str] = None
    recorded_by: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ===========================================================================
# BudgetLineItem
# ===========================================================================

class BudgetLineItemCreate(BaseModel):
    category: BudgetCategory
    name: str
    description: Optional[str] = None
    allocated_amount: Decimal = Field(default=Decimal("0"), ge=0)
    notes: Optional[str] = None


class BudgetLineItemUpdate(BaseModel):
    category: Optional[BudgetCategory] = None
    name: Optional[str] = None
    description: Optional[str] = None
    allocated_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class BudgetLineItemResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    budget_id: UUID
    category: BudgetCategory
    name: str
    description: Optional[str] = None
    allocated_amount: Decimal
    spent_amount: Decimal
    forecasted_amount: Decimal
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    transactions: List[BudgetTransactionResponse] = []

    model_config = {"from_attributes": True}


class BudgetLineItemSummary(BaseModel):
    id: UUID
    budget_id: UUID
    category: BudgetCategory
    name: str
    allocated_amount: Decimal
    spent_amount: Decimal
    forecasted_amount: Decimal
    remaining: Decimal = Decimal("0")

    model_config = {"from_attributes": True}


# ===========================================================================
# BudgetForecast
# ===========================================================================

class BudgetForecastCreate(BaseModel):
    line_item_id: Optional[UUID] = None
    forecast_method: ForecastMethod = ForecastMethod.LINEAR
    forecasted_amount: Decimal = Field(..., ge=0)
    confidence_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    scenario_label: Optional[str] = None
    rationale: Optional[str] = None


class BudgetForecastResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    budget_id: UUID
    line_item_id: Optional[UUID] = None
    forecast_method: ForecastMethod
    forecasted_amount: Decimal
    confidence_pct: Optional[Decimal] = None
    scenario_label: Optional[str] = None
    rationale: Optional[str] = None
    generated_by: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ===========================================================================
# Budget (master record)
# ===========================================================================

class BudgetCreate(BaseModel):
    fiscal_year_id: UUID
    school_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    status: BudgetStatus = BudgetStatus.DRAFT
    total_allocated: Decimal = Field(default=Decimal("0"), ge=0)
    notes: Optional[str] = None
    line_items: List[BudgetLineItemCreate] = []


class BudgetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[BudgetStatus] = None
    total_allocated: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class BudgetResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    fiscal_year_id: UUID
    school_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    status: BudgetStatus
    total_allocated: Decimal
    total_spent: Decimal
    total_forecasted: Decimal
    notes: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    line_items: List[BudgetLineItemResponse] = []

    model_config = {"from_attributes": True}


class BudgetSummary(BaseModel):
    id: UUID
    tenant_id: UUID
    fiscal_year_id: UUID
    school_id: Optional[UUID] = None
    name: str
    status: BudgetStatus
    total_allocated: Decimal
    total_spent: Decimal
    total_forecasted: Decimal
    utilization_pct: Decimal = Decimal("0")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ===========================================================================
# Budget overview / analytics response
# ===========================================================================

class BudgetOverview(BaseModel):
    """Aggregated budget health for a fiscal year."""
    fiscal_year: str
    total_budgets: int
    total_allocated: Decimal
    total_spent: Decimal
    total_forecasted: Decimal
    utilization_pct: Decimal
    over_budget_count: int
    by_category: List[dict]