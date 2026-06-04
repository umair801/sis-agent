"""
Budget service layer for AgAI_30 SIS.
Handles fiscal years, budgets, line items, transactions, and forecasting.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import FiscalYear, Budget, BudgetLineItem, BudgetTransaction, BudgetForecast
from app.schemas.budget import (
    FiscalYearCreate, FiscalYearUpdate,
    BudgetCreate, BudgetUpdate,
    BudgetLineItemCreate, BudgetLineItemUpdate,
    BudgetTransactionCreate,
    BudgetForecastCreate,
    BudgetSummary, BudgetOverview,
)
from app.core.logging import logger


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _budget_load_options():
    return [
        selectinload(Budget.line_items).selectinload(BudgetLineItem.transactions)
    ]


def _utilization(allocated: Decimal, spent: Decimal) -> Decimal:
    if not allocated or allocated == 0:
        return Decimal("0")
    return round((spent / allocated) * 100, 2)


# ---------------------------------------------------------------------------
# Fiscal Year
# ---------------------------------------------------------------------------

class FiscalYearService:

    @staticmethod
    async def create_fiscal_year(
        db: AsyncSession,
        tenant_id: UUID,
        payload: FiscalYearCreate,
    ) -> FiscalYear:
        # Only one current fiscal year allowed
        if payload.is_current:
            await db.execute(
                update(FiscalYear)
                .where(FiscalYear.tenant_id == tenant_id)
                .values(is_current=False)
            )
        fy = FiscalYear(tenant_id=tenant_id, **payload.model_dump())
        db.add(fy)
        await db.commit()
        await db.refresh(fy)
        return fy

    @staticmethod
    async def list_fiscal_years(
        db: AsyncSession,
        tenant_id: UUID,
    ) -> List[FiscalYear]:
        result = await db.execute(
            select(FiscalYear)
            .where(FiscalYear.tenant_id == tenant_id)
            .order_by(FiscalYear.start_date.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_fiscal_year(
        db: AsyncSession,
        tenant_id: UUID,
        fy_id: UUID,
    ) -> Optional[FiscalYear]:
        result = await db.execute(
            select(FiscalYear).where(
                FiscalYear.id == fy_id,
                FiscalYear.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_current_fiscal_year(
        db: AsyncSession,
        tenant_id: UUID,
    ) -> Optional[FiscalYear]:
        result = await db.execute(
            select(FiscalYear).where(
                FiscalYear.tenant_id == tenant_id,
                FiscalYear.is_current == True,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_fiscal_year(
        db: AsyncSession,
        tenant_id: UUID,
        fy_id: UUID,
        payload: FiscalYearUpdate,
    ) -> Optional[FiscalYear]:
        result = await db.execute(
            select(FiscalYear).where(
                FiscalYear.id == fy_id,
                FiscalYear.tenant_id == tenant_id,
            )
        )
        fy = result.scalar_one_or_none()
        if not fy:
            return None
        if payload.is_current:
            await db.execute(
                update(FiscalYear)
                .where(FiscalYear.tenant_id == tenant_id)
                .values(is_current=False)
            )
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(fy, field, value)
        await db.commit()
        await db.refresh(fy)
        return fy


# ---------------------------------------------------------------------------
# Budget CRUD
# ---------------------------------------------------------------------------

class BudgetService:

    @staticmethod
    async def create_budget(
        db: AsyncSession,
        tenant_id: UUID,
        payload: BudgetCreate,
        created_by: UUID,
    ) -> Budget:
        # Verify fiscal year belongs to tenant
        fy = await db.get(FiscalYear, payload.fiscal_year_id)
        if not fy or fy.tenant_id != tenant_id:
            raise ValueError("Fiscal year not found in this district")

        budget_data = payload.model_dump(exclude={"line_items"})
        budget = Budget(
            tenant_id=tenant_id,
            created_by=created_by,
            **budget_data,
        )
        db.add(budget)
        await db.flush()

        for item in payload.line_items:
            db.add(BudgetLineItem(
                tenant_id=tenant_id,
                budget_id=budget.id,
                **item.model_dump(),
            ))

        await db.commit()

        result = await db.execute(
            select(Budget).where(Budget.id == budget.id)
            .options(*_budget_load_options())
        )
        return result.scalar_one()

    @staticmethod
    async def get_budget(
        db: AsyncSession,
        tenant_id: UUID,
        budget_id: UUID,
    ) -> Optional[Budget]:
        result = await db.execute(
            select(Budget)
            .where(Budget.id == budget_id, Budget.tenant_id == tenant_id)
            .options(*_budget_load_options())
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_budgets(
        db: AsyncSession,
        tenant_id: UUID,
        fiscal_year_id: Optional[UUID] = None,
        school_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Budget], int]:
        query = select(Budget).where(Budget.tenant_id == tenant_id)
        if fiscal_year_id:
            query = query.where(Budget.fiscal_year_id == fiscal_year_id)
        if school_id:
            query = query.where(Budget.school_id == school_id)

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        result = await db.execute(
            query.order_by(Budget.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def update_budget(
        db: AsyncSession,
        tenant_id: UUID,
        budget_id: UUID,
        payload: BudgetUpdate,
    ) -> Optional[Budget]:
        result = await db.execute(
            select(Budget).where(Budget.id == budget_id, Budget.tenant_id == tenant_id)
        )
        budget = result.scalar_one_or_none()
        if not budget:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(budget, field, value)
        await db.commit()
        result = await db.execute(
            select(Budget).where(Budget.id == budget_id)
            .options(*_budget_load_options())
        )
        return result.scalar_one()

    @staticmethod
    async def delete_budget(
        db: AsyncSession,
        tenant_id: UUID,
        budget_id: UUID,
    ) -> bool:
        result = await db.execute(
            select(Budget).where(Budget.id == budget_id, Budget.tenant_id == tenant_id)
        )
        budget = result.scalar_one_or_none()
        if not budget:
            return False
        if budget.status not in ("draft",):
            raise ValueError("Only DRAFT budgets can be deleted.")
        await db.delete(budget)
        await db.commit()
        return True

    # ------------------------------------------------------------------
    # Budget overview / analytics
    # ------------------------------------------------------------------

    @staticmethod
    async def get_budget_overview(
        db: AsyncSession,
        tenant_id: UUID,
        fiscal_year_id: UUID,
    ) -> BudgetOverview:
        fy_result = await db.execute(
            select(FiscalYear).where(
                FiscalYear.id == fiscal_year_id,
                FiscalYear.tenant_id == tenant_id,
            )
        )
        fy = fy_result.scalar_one_or_none()
        if not fy:
            raise ValueError("Fiscal year not found")

        budgets_result = await db.execute(
            select(Budget)
            .where(Budget.tenant_id == tenant_id, Budget.fiscal_year_id == fiscal_year_id)
            .options(*_budget_load_options())
        )
        budgets = list(budgets_result.scalars().all())

        total_allocated  = sum(b.total_allocated  or Decimal(0) for b in budgets)
        total_spent      = sum(b.total_spent      or Decimal(0) for b in budgets)
        total_forecasted = sum(b.total_forecasted or Decimal(0) for b in budgets)

        # Category breakdown
        category_totals: dict = {}
        for b in budgets:
            for li in b.line_items:
                cat = li.category if isinstance(li.category, str) else li.category.value
                if cat not in category_totals:
                    category_totals[cat] = {
                        "category": cat,
                        "allocated": Decimal(0),
                        "spent": Decimal(0),
                    }
                category_totals[cat]["allocated"] += li.allocated_amount or Decimal(0)
                category_totals[cat]["spent"]     += li.spent_amount     or Decimal(0)

        over_budget = sum(
            1 for b in budgets
            if (b.total_spent or 0) > (b.total_allocated or 0)
        )

        return BudgetOverview(
            fiscal_year=fy.name,
            total_budgets=len(budgets),
            total_allocated=total_allocated,
            total_spent=total_spent,
            total_forecasted=total_forecasted,
            utilization_pct=_utilization(total_allocated, total_spent),
            over_budget_count=over_budget,
            by_category=list(category_totals.values()),
        )


# ---------------------------------------------------------------------------
# Line Items
# ---------------------------------------------------------------------------

class BudgetLineItemService:

    @staticmethod
    async def add_line_item(
        db: AsyncSession,
        tenant_id: UUID,
        budget_id: UUID,
        payload: BudgetLineItemCreate,
    ) -> BudgetLineItem:
        item = BudgetLineItem(
            tenant_id=tenant_id,
            budget_id=budget_id,
            **payload.model_dump(),
        )
        db.add(item)
        await db.commit()
        result = await db.execute(
            select(BudgetLineItem)
            .where(BudgetLineItem.id == item.id)
            .options(selectinload(BudgetLineItem.transactions))
        )
        return result.scalar_one()

    @staticmethod
    async def update_line_item(
        db: AsyncSession,
        tenant_id: UUID,
        item_id: UUID,
        payload: BudgetLineItemUpdate,
    ) -> Optional[BudgetLineItem]:
        result = await db.execute(
            select(BudgetLineItem).where(
                BudgetLineItem.id == item_id,
                BudgetLineItem.tenant_id == tenant_id,
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        await db.commit()
        result = await db.execute(
            select(BudgetLineItem)
            .where(BudgetLineItem.id == item_id)
            .options(selectinload(BudgetLineItem.transactions))
        )
        return result.scalar_one()

    @staticmethod
    async def delete_line_item(
        db: AsyncSession,
        tenant_id: UUID,
        item_id: UUID,
    ) -> bool:
        result = await db.execute(
            select(BudgetLineItem).where(
                BudgetLineItem.id == item_id,
                BudgetLineItem.tenant_id == tenant_id,
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            return False
        await db.delete(item)
        await db.commit()
        return True


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

class BudgetTransactionService:

    @staticmethod
    async def add_transaction(
        db: AsyncSession,
        tenant_id: UUID,
        line_item_id: UUID,
        payload: BudgetTransactionCreate,
        recorded_by: UUID,
    ) -> BudgetTransaction:
        # Fetch line item to update spent_amount
        result = await db.execute(
            select(BudgetLineItem).where(
                BudgetLineItem.id == line_item_id,
                BudgetLineItem.tenant_id == tenant_id,
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            raise ValueError("Line item not found")

        txn = BudgetTransaction(
            tenant_id=tenant_id,
            line_item_id=line_item_id,
            recorded_by=recorded_by,
            **payload.model_dump(),
        )
        db.add(txn)

        # Update line item spent_amount
        if payload.transaction_type.value == "expense":
            item.spent_amount = (item.spent_amount or Decimal(0)) + payload.amount
        elif payload.transaction_type.value == "refund":
            item.spent_amount = max(
                Decimal(0),
                (item.spent_amount or Decimal(0)) - payload.amount,
            )

        await db.commit()

        # Recalculate parent budget totals
        await BudgetTransactionService._sync_budget_totals(db, item.budget_id)

        await db.refresh(txn)
        return txn

    @staticmethod
    async def _sync_budget_totals(db: AsyncSession, budget_id: UUID) -> None:
        """Recalculate and persist budget-level totals from line items."""
        result = await db.execute(
            select(
                func.sum(BudgetLineItem.spent_amount),
                func.sum(BudgetLineItem.forecasted_amount),
            ).where(BudgetLineItem.budget_id == budget_id)
        )
        row = result.one()
        total_spent      = row[0] or Decimal(0)
        total_forecasted = row[1] or Decimal(0)

        budget_result = await db.execute(
            select(Budget).where(Budget.id == budget_id)
        )
        budget = budget_result.scalar_one_or_none()
        if budget:
            budget.total_spent      = total_spent
            budget.total_forecasted = total_forecasted
            await db.commit()


# ---------------------------------------------------------------------------
# Forecasts
# ---------------------------------------------------------------------------

class BudgetForecastService:

    @staticmethod
    async def create_forecast(
        db: AsyncSession,
        tenant_id: UUID,
        budget_id: UUID,
        payload: BudgetForecastCreate,
        generated_by: UUID,
    ) -> BudgetForecast:
        forecast = BudgetForecast(
            tenant_id=tenant_id,
            budget_id=budget_id,
            generated_by=generated_by,
            **payload.model_dump(),
        )
        db.add(forecast)

        # Update line item forecasted_amount if linked
        if payload.line_item_id:
            result = await db.execute(
                select(BudgetLineItem).where(BudgetLineItem.id == payload.line_item_id)
            )
            item = result.scalar_one_or_none()
            if item:
                item.forecasted_amount = payload.forecasted_amount

        await db.commit()
        await BudgetTransactionService._sync_budget_totals(db, budget_id)
        await db.refresh(forecast)
        return forecast

    @staticmethod
    async def list_forecasts(
        db: AsyncSession,
        tenant_id: UUID,
        budget_id: UUID,
    ) -> List[BudgetForecast]:
        result = await db.execute(
            select(BudgetForecast).where(
                BudgetForecast.budget_id == budget_id,
                BudgetForecast.tenant_id == tenant_id,
            ).order_by(BudgetForecast.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def generate_linear_forecast(
        db: AsyncSession,
        tenant_id: UUID,
        budget_id: UUID,
        generated_by: UUID,
    ) -> List[BudgetForecast]:
        """
        Simple linear projection: if X% of fiscal year has elapsed,
        project final spend = current_spend / elapsed_pct.
        Creates one forecast per line item.
        """
        # Get budget with fiscal year
        result = await db.execute(
            select(Budget)
            .where(Budget.id == budget_id, Budget.tenant_id == tenant_id)
            .options(selectinload(Budget.line_items))
        )
        budget = result.scalar_one_or_none()
        if not budget:
            raise ValueError("Budget not found")

        fy_result = await db.execute(
            select(FiscalYear).where(FiscalYear.id == budget.fiscal_year_id)
        )
        fy = fy_result.scalar_one_or_none()
        if not fy:
            raise ValueError("Fiscal year not found")

        today = date.today()
        total_days   = max((fy.end_date - fy.start_date).days, 1)
        elapsed_days = max((today - fy.start_date).days, 1)
        elapsed_pct  = min(Decimal(str(elapsed_days)) / Decimal(str(total_days)), Decimal("1"))

        forecasts = []
        for item in budget.line_items:
            if elapsed_pct > 0:
                projected = round(
                    (item.spent_amount or Decimal(0)) / elapsed_pct, 2
                )
            else:
                projected = item.allocated_amount or Decimal(0)

            confidence = round(elapsed_pct * 100, 2)
            forecast = BudgetForecast(
                tenant_id=tenant_id,
                budget_id=budget_id,
                line_item_id=item.id,
                forecast_method="linear",
                forecasted_amount=projected,
                confidence_pct=confidence,
                scenario_label="Linear Projection",
                rationale=(
                    f"{float(elapsed_pct*100):.1f}% of fiscal year elapsed. "
                    f"Current spend ${item.spent_amount:.2f} projects to ${projected:.2f}."
                ),
                generated_by=generated_by,
            )
            db.add(forecast)
            item.forecasted_amount = projected
            forecasts.append(forecast)

        await db.commit()
        await BudgetTransactionService._sync_budget_totals(db, budget_id)
        return forecasts