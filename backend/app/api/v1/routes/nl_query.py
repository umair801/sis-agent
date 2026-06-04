"""
C1 — NL Query API Route
POST /api/v1/query/ask  — accepts a natural language question and returns results + summary
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.services.nl_query_service import handle_nl_query

router = APIRouter(prefix="/query", tags=["AI Query"])


class NLQueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Plain English question about school data",
        examples=["How many students were absent last week?"],
    )
    school_id: Optional[str] = Field(
        None,
        description="Optional: scope query to a specific school",
    )
    context: Optional[dict] = Field(
        None,
        description="Optional: additional context hints (e.g., date range, module name)",
    )


class NLQueryResponse(BaseModel):
    success: bool
    question: str
    intent: str
    confidence: Optional[float] = None
    row_count: int
    rows: list[dict]
    summary: str
    error: Optional[str] = None
    duration_ms: int


@router.post(
    "/ask",
    response_model=NLQueryResponse,
    summary="Ask a natural language question about school data",
    description=(
        "Accepts a plain-English question, generates a safe parameterized SQL query, "
        "executes it scoped to the caller's tenant, and returns AI-summarized results. "
        "Only SELECT queries are permitted. All results are tenant-isolated."
    ),
)
async def ask_nl_query(
    payload: NLQueryRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NLQueryResponse:
    tenant_id: str = current_user.tenant_id
    user_role: str = current_user.role

    result = await handle_nl_query(
        question=payload.question,
        tenant_id=tenant_id,
        db=db,
        user_role=user_role,
        school_id=payload.school_id,
        context=payload.context,
    )

    return NLQueryResponse(**result)