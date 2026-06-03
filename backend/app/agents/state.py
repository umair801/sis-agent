from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    # Conversation
    messages: Annotated[list, add_messages]

    # Request context
    user_query: str
    tenant_id: str
    user_id: str
    role: str

    # Routing
    intent: Optional[str]
    target_agent: Optional[str]

    # Module data
    module: Optional[str]
    module_data: Optional[dict]

    # Response
    final_response: Optional[str]
    citations: Optional[list]
    error: Optional[str]

    # Control
    iteration_count: int
