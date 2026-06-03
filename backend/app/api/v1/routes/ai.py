from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.agents.graph import sis_graph
from app.agents.state import AgentState
from app.core.dependencies import get_current_user
from app.schemas.auth import TokenPayload
from app.services.claude_service import summarize_data, nl_to_filters

router = APIRouter(prefix="/ai", tags=["AI"])


class QueryRequest(BaseModel):
    query: str
    module: str = "general"


class QueryResponse(BaseModel):
    response: str
    intent: str
    target_agent: str
    module: str


class SummarizeRequest(BaseModel):
    data: dict | list
    context: str


class NLFilterRequest(BaseModel):
    query: str
    module: str


@router.post("/query", response_model=QueryResponse)
async def ai_query(
    payload: QueryRequest,
    current_user: TokenPayload = Depends(get_current_user),
):
    initial_state: AgentState = {
        "messages": [],
        "user_query": payload.query,
        "tenant_id": current_user.tenant_id,
        "user_id": current_user.sub,
        "role": current_user.role,
        "intent": None,
        "target_agent": None,
        "module": payload.module,
        "module_data": None,
        "final_response": None,
        "citations": None,
        "error": None,
        "iteration_count": 0,
    }
    result = await sis_graph.ainvoke(initial_state)
    return QueryResponse(
        response=result.get("final_response") or "No response generated.",
        intent=result.get("intent") or "",
        target_agent=result.get("target_agent") or "query_agent",
        module=result.get("module") or payload.module,
    )


@router.post("/summarize", tags=["AI"])
async def summarize(
    payload: SummarizeRequest,
    current_user: TokenPayload = Depends(get_current_user),
):
    summary = await summarize_data(
        data=payload.data,
        context=payload.context,
        role=current_user.role,
    )
    return {"summary": summary, "role": current_user.role}


@router.post("/nl-filters", tags=["AI"])
async def nl_filters(
    payload: NLFilterRequest,
    current_user: TokenPayload = Depends(get_current_user),
):
    filters = await nl_to_filters(
        query=payload.query,
        module=payload.module,
        tenant_id=current_user.tenant_id,
        role=current_user.role,
    )
    return {"filters": filters, "module": payload.module}
