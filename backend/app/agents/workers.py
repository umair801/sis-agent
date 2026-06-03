from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from app.agents.state import AgentState
from app.agents.llm import get_llm
import structlog

logger = structlog.get_logger()


def _build_context(state: AgentState) -> str:
    return f"""
Tenant ID: {state['tenant_id']}
User Role: {state['role']}
Module: {state.get('module', 'general')}
Intent: {state.get('intent', '')}
"""


async def query_agent_node(state: AgentState) -> AgentState:
    logger.info("Query agent processing", intent=state.get("intent"))
    llm = get_llm()

    system = f"""You are the SIS query agent for Datawebify Student Information System.
You answer natural language questions about student data based on the user's role and tenant.
Context: {_build_context(state)}
Be concise, accurate, and role-appropriate. Never expose data outside the tenant scope."""

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=state["user_query"])
    ]

    try:
        response = await llm.ainvoke(messages)
        return {**state, "final_response": response.content, "error": None}
    except Exception as e:
        logger.error("Query agent failed", error=str(e))
        return {**state, "final_response": None, "error": str(e)}


async def report_agent_node(state: AgentState) -> AgentState:
    logger.info("Report agent processing", intent=state.get("intent"))
    llm = get_llm()

    system = f"""You are the SIS report generation agent for Datawebify Student Information System.
You generate structured reports on attendance, grades, and compliance.
Context: {_build_context(state)}
Format reports clearly with sections, summaries, and actionable insights."""

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=state["user_query"])
    ]

    try:
        response = await llm.ainvoke(messages)
        return {**state, "final_response": response.content, "error": None}
    except Exception as e:
        logger.error("Report agent failed", error=str(e))
        return {**state, "final_response": None, "error": str(e)}


async def compliance_agent_node(state: AgentState) -> AgentState:
    logger.info("Compliance agent processing", intent=state.get("intent"))
    llm = get_llm()

    system = f"""You are the SIS compliance agent for Datawebify Student Information System.
You monitor IEP deadlines, IDEA/FERPA compliance, and SpEd requirements.
Context: {_build_context(state)}
Flag any compliance risks clearly and suggest corrective actions."""

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=state["user_query"])
    ]

    try:
        response = await llm.ainvoke(messages)
        return {**state, "final_response": response.content, "error": None}
    except Exception as e:
        logger.error("Compliance agent failed", error=str(e))
        return {**state, "final_response": None, "error": str(e)}


async def forecast_agent_node(state: AgentState) -> AgentState:
    logger.info("Forecast agent processing", intent=state.get("intent"))
    llm = get_llm()

    system = f"""You are the SIS forecasting agent for Datawebify Student Information System.
You analyze enrollment trends, budget projections, and resource planning scenarios.
Context: {_build_context(state)}
Provide data-driven forecasts with confidence levels and assumptions clearly stated."""

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=state["user_query"])
    ]

    try:
        response = await llm.ainvoke(messages)
        return {**state, "final_response": response.content, "error": None}
    except Exception as e:
        logger.error("Forecast agent failed", error=str(e))
        return {**state, "final_response": None, "error": str(e)}


async def rag_agent_node(state: AgentState) -> AgentState:
    logger.info("RAG agent processing", intent=state.get("intent"))
    llm = get_llm()

    system = f"""You are the SIS document search agent for Datawebify Student Information System.
You answer questions about district policies, handbooks, and IEP documents.
Context: {_build_context(state)}
Cite your sources and indicate if information is not found in available documents."""

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=state["user_query"])
    ]

    try:
        response = await llm.ainvoke(messages)
        return {**state, "final_response": response.content, "error": None}
    except Exception as e:
        logger.error("RAG agent failed", error=str(e))
        return {**state, "final_response": None, "error": str(e)}
