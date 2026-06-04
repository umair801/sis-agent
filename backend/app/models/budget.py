"""
Budget and resource allocation models for AgAI_30 SIS.
Covers: fiscal years, budget categories, line items, actuals, forecasts.
"""

import uuid
from datetime import date, datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Text, Boolean, Date, DateTime,
    ForeignKey, Numeric, Integer, Index, UniqueConstraint
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship as sa_relationship
from sqlalchemy.sql import func

from app.db.database import Base


# ---------------------------------------------------------------------------
# Enumerations (kept inline — no circular import risk, no DB enum types needed)
# ---------------------------------------------------------------------------

class BudgetStatus(str, PyEnum):
    DRAFT     = "draft"
    APPROVED  = "approved"
    ACTIVE    = "active"
    CLOSED    = "closed"


class BudgetCategory(str, PyEnum):
    PERSONNEL          = "personnel"
    BENEFITS           = "benefits"
    SUPPLIES           = "supplies"
    EQUIPMENT          = "equipment"
    FACILITIES         = "facilities"
    TRANSPORTATION     = "transportation"
    PROFESSIONAL_DEV   = "professional_dev"
    TECHNOLOGY         = "technology"
    SPECIAL_EDUCATION  = "special_education"
    CONTRACTED_SERVICES = "contracted_services"
    OTHER              = "other"


class TransactionType(str, PyEnum):
    EXPENSE    = "expense"
    TRANSFER   = "transfer"
    ADJUSTMENT = "adjustment"
    REFUND     = "refund"


class ForecastMethod(str, PyEnum):
    LINEAR       = "linear"
    PERCENT_USED = "percent_used"
    AI_GENERATED = "ai_generated"


# ---------------------------------------------------------------------------
# sis_fiscal_year
# ---------------------------------------------------------------------------

class FiscalYear(Base):
    __tablename__ = "sis_fiscal_year"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id   = Column(UUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    name        = Column(String(50), nullable=False)        # e.g. "2024-2025"
    start_date  = Column(Date, nullable=False)
    end_date    = Column(Date, nullable=False)
    is_current  = Column(Boolean, nullable=False, default=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    budgets     = sa_relationship("Budget", back_populates="fiscal_year", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_sis_fiscal_year_tenant_name"),
        Index("ix_sis_fiscal_year_tenant", "tenant_id"),
    )


# ---------------------------------------------------------------------------
# sis_budget  (top-level budget for a fiscal year + school/department)
# ---------------------------------------------------------------------------

class Budget(Base):
    __tablename__ = "sis_budget"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id        = Column(UUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    fiscal_year_id   = Column(UUID(as_uuid=True), ForeignKey("sis_fiscal_year.id", ondelete="CASCADE"), nullable=False)
    school_id        = Column(UUID(as_uuid=True), ForeignKey("sis_school.id", ondelete="SET NULL"), nullable=True)
    name             = Column(String(255), nullable=False)
    description      = Column(Text, nullable=True)
    status           = Column(SAEnum(*[e.value for e in BudgetStatus], name="sis_budget_status", create_type=False), nullable=False, default=BudgetStatus.DRAFT.value)
    total_allocated  = Column(Numeric(14, 2), nullable=False, default=0)
    total_spent      = Column(Numeric(14, 2), nullable=False, default=0)
    total_forecasted = Column(Numeric(14, 2), nullable=False, default=0)
    notes            = Column(Text, nullable=True)
    created_by       = Column(UUID(as_uuid=True), ForeignKey("sis_user.id"), nullable=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    fiscal_year  = sa_relationship("FiscalYear", back_populates="budgets")
    school       = sa_relationship("School", foreign_keys=[school_id])
    line_items   = sa_relationship("BudgetLineItem", back_populates="budget", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sis_budget_tenant_year", "tenant_id", "fiscal_year_id"),
    )


# ---------------------------------------------------------------------------
# sis_budget_line_item  (category-level allocation within a budget)
# ---------------------------------------------------------------------------

class BudgetLineItem(Base):
    __tablename__ = "sis_budget_line_item"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id        = Column(UUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    budget_id        = Column(UUID(as_uuid=True), ForeignKey("sis_budget.id", ondelete="CASCADE"), nullable=False)
    category         = Column(SAEnum(*[e.value for e in BudgetCategory], name="sis_budget_category", create_type=False), nullable=False)
    name             = Column(String(255), nullable=False)
    description      = Column(Text, nullable=True)
    allocated_amount = Column(Numeric(14, 2), nullable=False, default=0)
    spent_amount     = Column(Numeric(14, 2), nullable=False, default=0)
    forecasted_amount = Column(Numeric(14, 2), nullable=False, default=0)
    notes            = Column(Text, nullable=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    budget       = sa_relationship("Budget", back_populates="line_items")
    transactions = sa_relationship("BudgetTransaction", back_populates="line_item", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sis_budget_line_item_budget", "budget_id"),
    )


# ---------------------------------------------------------------------------
# sis_budget_transaction  (actual spend entries)
# ---------------------------------------------------------------------------

class BudgetTransaction(Base):
    __tablename__ = "sis_budget_transaction"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id        = Column(UUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    line_item_id     = Column(UUID(as_uuid=True), ForeignKey("sis_budget_line_item.id", ondelete="CASCADE"), nullable=False)
    transaction_type = Column(SAEnum(*[e.value for e in TransactionType], name="sis_transaction_type", create_type=False), nullable=False, default=TransactionType.EXPENSE.value)
    amount           = Column(Numeric(14, 2), nullable=False)
    transaction_date = Column(Date, nullable=False)
    vendor           = Column(String(255), nullable=True)
    description      = Column(Text, nullable=True)
    reference_number = Column(String(100), nullable=True)
    recorded_by      = Column(UUID(as_uuid=True), ForeignKey("sis_user.id"), nullable=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())

    line_item = sa_relationship("BudgetLineItem", back_populates="transactions")

    __table_args__ = (
        Index("ix_sis_budget_transaction_line_item", "line_item_id"),
        Index("ix_sis_budget_transaction_date", "transaction_date"),
    )


# ---------------------------------------------------------------------------
# sis_budget_forecast  (AI or manual scenario projections)
# ---------------------------------------------------------------------------

class BudgetForecast(Base):
    __tablename__ = "sis_budget_forecast"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id        = Column(UUID(as_uuid=True), ForeignKey("sis_tenant.id", ondelete="CASCADE"), nullable=False)
    budget_id        = Column(UUID(as_uuid=True), ForeignKey("sis_budget.id", ondelete="CASCADE"), nullable=False)
    line_item_id     = Column(UUID(as_uuid=True), ForeignKey("sis_budget_line_item.id", ondelete="CASCADE"), nullable=True)
    forecast_method  = Column(SAEnum(*[e.value for e in ForecastMethod], name="sis_forecast_method", create_type=False), nullable=False, default=ForecastMethod.LINEAR.value)
    forecasted_amount = Column(Numeric(14, 2), nullable=False)
    confidence_pct   = Column(Numeric(5, 2), nullable=True)   # 0-100
    scenario_label   = Column(String(100), nullable=True)     # e.g. "Base", "Worst Case", "Best Case"
    rationale        = Column(Text, nullable=True)            # AI-generated explanation
    generated_by     = Column(UUID(as_uuid=True), ForeignKey("sis_user.id"), nullable=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_sis_budget_forecast_budget", "budget_id"),
    )