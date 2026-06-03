from app.agents.state import AgentState
from app.agents.llm import get_llm
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.logging import logger
import json

VALIDATOR_SYSTEM = """You are a quality validation agent for Datawebify Student Information System.
Evaluate the AI response and return ONLY a JSON object with this exact format:
{
    "passed": true or false,
    "score": 0-100,
    "issues": ["list of issues if any"],
    "suggestion": "improvement suggestion if failed"
}

Validation criteria:
- Response must directly address the user query
- Response must be appropriate for the user role
- Response must not expose data from other tenants
- Response must be factual and not hallucinated
- Response must be at least 20 words
- Response must not contain error messages or stack traces"""


async def validate_response(state: AgentState) -> AgentState:
    response = state.get("final_response", "")
    query = state.get("user_query", "")
    role = state.get("role", "")

    # Fast checks before calling LLM
    issues = []

    if not response:
        return {
            **state,
            "final_response": "I was unable to generate a response. Please try again.",
            "error": "Empty response from agent",
        }

    if len(response.split()) < 10:
        issues.append("Response too short")

    if any(word in response.lower() for word in ["traceback", "exception", "error:", "stack trace"]):
        issues.append("Response contains error output")

    if state.get("error"):
        issues.append(f"Agent reported error: {state['error']}")

    # If fast checks already found critical issues, return fallback
    if "Response contains error output" in issues:
        return {
            **state,
            "final_response": "I encountered an issue processing your request. Please rephrase and try again.",
            "error": "; ".join(issues),
        }

    # LLM quality check for substantive responses
    if len(response.split()) >= 10 and not issues:
        try:
            llm = get_llm()
            messages = [
                SystemMessage(content=VALIDATOR_SYSTEM),
                HumanMessage(content=f"""
User Query: {query}
User Role: {role}
AI Response: {response}

Validate this response.
""")
            ]
            result = await llm.ainvoke(messages)
            raw = result.content.strip()

            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            validation = json.loads(raw.strip())
            score = validation.get("score", 100)
            passed = validation.get("passed", True)

            logger.info(
                "Response validated",
                passed=passed,
                score=score,
                issues=validation.get("issues", []),
            )

            if not passed and score < 40:
                suggestion = validation.get("suggestion", "")
                return {
                    **state,
                    "final_response": f"{response}\n\n[Note: {suggestion}]" if suggestion else response,
                    "error": "; ".join(validation.get("issues", [])),
                }

        except Exception as e:
            logger.warning("Validator LLM check failed, passing through", error=str(e))

    return {**state, "error": "; ".join(issues) if issues else None}
