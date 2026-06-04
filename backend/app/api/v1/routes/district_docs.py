"""
C6 -- District Documents RAG API Routes
GET  /api/v1/district-docs/categories   -- list document categories
POST /api/v1/district-docs/query        -- query district documents
"""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.services.district_docs_service import (
    query_district_docs,
    DOC_CATEGORIES,
    ROLE_DOC_ACCESS,
)

router = APIRouter(prefix="/district-docs", tags=["District Documents"])


class DocQueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=5,
        max_length=500,
        examples=["What is the district policy on excused absences?"],
    )
    doc_category: Optional[str] = Field(
        None,
        description="Optional: filter to a specific document category",
    )
    k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of document chunks to retrieve",
    )


@router.get(
    "/categories",
    summary="List document categories and role access",
)
async def list_categories(
    current_user=Depends(get_current_user),
):
    user_role: str = current_user.role
    allowed = ROLE_DOC_ACCESS.get(user_role, ["handbook", "general"])
    return {
        "all_categories": DOC_CATEGORIES,
        "your_accessible_categories": {
            k: v for k, v in DOC_CATEGORIES.items() if k in allowed
        },
        "your_role": user_role,
    }


@router.post(
    "/query",
    summary="Query district documents using natural language",
    description=(
        "Searches district document knowledge base using semantic similarity, "
        "then uses Claude to generate a cited answer grounded in the document text. "
        "Access is scoped by user role. Optionally filter by document category."
    ),
)
async def query_docs(
    payload: DocQueryRequest,
    current_user=Depends(get_current_user),
):
    tenant_id: str = str(current_user.tenant_id)
    user_role: str = current_user.role

    return await query_district_docs(
        question=payload.question,
        tenant_id=tenant_id,
        user_role=user_role,
        doc_category=payload.doc_category,
        k=payload.k,
    )