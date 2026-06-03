from anthropic import AsyncAnthropic
from app.core.config import settings
from app.core.logging import logger
from tenacity import retry, stop_after_attempt, wait_exponential
import json

client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def call_claude(
    prompt: str,
    system: str = "",
    max_tokens: int = 1024,
    temperature: float = 0.0,
) -> str:
    try:
        message = await client.messages.create(
            model=settings.PRIMARY_LLM,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or "You are a helpful AI assistant for a Student Information System.",
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as e:
        logger.error("Claude API call failed", error=str(e))
        raise


async def summarize_data(
    data: dict | list,
    context: str,
    role: str = "DistrictAdmin",
) -> str:
    system = f"""You are an AI assistant for Datawebify Student Information System.
Summarize the provided data clearly and concisely for a {role}.
Focus on key insights, trends, and any items needing attention.
Use plain language. No markdown headers. Keep it under 200 words."""

    prompt = f"""Context: {context}

Data to summarize:
{json.dumps(data, indent=2, default=str)}

Provide a clear summary with the most important insights."""

    return await call_claude(prompt, system=system, max_tokens=512)


async def nl_to_filters(
    query: str,
    module: str,
    tenant_id: str,
    role: str,
) -> dict:
    system = """You are a query parser for a Student Information System.
Convert natural language queries into structured filter parameters.
Respond ONLY with a valid JSON object. No explanation. No markdown."""

    module_schemas = {
        "students": '{"name": null, "grade_level": null, "enrollment_status": null, "limit": 50}',
        "attendance": '{"student_id": null, "date_from": null, "date_to": null, "status": null, "limit": 50}',
        "gradebook": '{"student_id": null, "subject": null, "grade_min": null, "grade_max": null, "limit": 50}',
        "scheduling": '{"teacher_id": null, "room": null, "period": null, "subject": null, "limit": 50}',
        "sped": '{"student_id": null, "iep_status": null, "deadline_within_days": null, "limit": 50}',
        "budget": '{"category": null, "fiscal_year": null, "amount_min": null, "amount_max": null, "limit": 50}',
    }

    schema = module_schemas.get(module, '{"query": null, "limit": 50}')

    prompt = f"""Module: {module}
User Role: {role}
Natural language query: "{query}"

Convert this into filter parameters matching this schema:
{schema}

Return only a JSON object with the relevant filters filled in. Use null for unused fields."""

    try:
        raw = await call_claude(prompt, system=system, max_tokens=256)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        logger.error("NL to filters failed", error=str(e))
        return {"error": str(e), "limit": 50}


async def generate_compliance_alert(
    record: dict,
    alert_type: str,
    tenant_id: str,
) -> dict:
    system = """You are a compliance officer AI for a Student Information System.
Analyze records for IDEA/FERPA compliance issues.
Respond ONLY with a valid JSON object."""

    prompt = f"""Alert type: {alert_type}
Record data: {json.dumps(record, indent=2, default=str)}

Analyze this record and return a JSON with:
{{
    "severity": "high|medium|low",
    "issue": "brief description of the compliance issue",
    "action_required": "what needs to be done",
    "deadline": "when it must be done by or null",
    "regulation": "which regulation applies"
}}"""

    try:
        raw = await call_claude(prompt, system=system, max_tokens=512)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        logger.error("Compliance alert generation failed", error=str(e))
        return {"severity": "low", "issue": str(e), "action_required": "Review manually"}
