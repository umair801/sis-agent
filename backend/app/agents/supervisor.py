from langchain_core.messages import HumanMessage, SystemMessage
from app.agents.state import AgentState
from app.agents.llm import get_llm
import structlog
import json

logger = structlog.get_logger()

SUPERVISOR_SYSTEM = """You are the SIS supervisor agent for Datawebify Student Information System.
Your job is to analyze the user query and route it to the correct specialized agent.

Available agents:
- query_agent: Natural language questions about students, grades, attendance, schedules
- report_agent: Generate reports (attendance summaries, grade reports, compliance reports)
- compliance_agent: IEP deadlines, IDEA/FERPA compliance checks, SpEd alerts
- forecast_agent: Enrollment trends, budget projections, scenario planning
- rag_agent: Policy lookups, handbook questions, document search

Respond ONLY with a JSON object in this exact format:
{
    "target_agent": "<agent_name>",
    "intent": "<one sentence description of what the user wants>",
    "module": "<students|attendance|gradebook|scheduling|sped|budget|communications>"
}"""


async def supervisor_node(state: AgentState) -> AgentState:
    logger.info("Supervisor routing", query=state["user_query"][:100])

    llm = get_llm()

    messages = [
        SystemMessage(content=SUPERVISOR_SYSTEM),
        HumanMessage(content=f"Route this query: {state['user_query']}")
    ]

    try:
        response = await llm.ainvoke(messages)
        raw = response.content.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        routing = json.loads(raw.strip())

        return {
            **state,
            "target_agent": routing.get("target_agent", "query_agent"),
            "intent": routing.get("intent", ""),
            "module": routing.get("module", "students"),
            "iteration_count": state.get("iteration_count", 0) + 1,
        }

    except Exception as e:
        logger.error("Supervisor routing failed", error=str(e))
        return {
            **state,
            "target_agent": "query_agent",
            "intent": state["user_query"],
            "module": "students",
            "error": str(e),
            "iteration_count": state.get("iteration_count", 0) + 1,
        }
