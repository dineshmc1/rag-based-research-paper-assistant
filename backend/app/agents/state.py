from typing import TypedDict, Annotated, List, Dict, Any, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """The state of the agent in the LangGraph."""
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Retrieved documents context
    documents: List[Dict[str, Any]]
    
    # Flags for control flow
    is_relevant: bool
    is_supported: bool
    
    # Retry counter
    retry_count: int
    
    # For reasoning and citations
    reasoning_trace: List[str]
    citations: List[Dict[str, Any]]
    
    # Generated artifacts (images, files)
    artifacts: List[Dict[str, Any]]
    
    # Execution Mode Control
    execution_mode: Literal["text", "python"]
    execution_status: str
    
    # Planning
    plan: List[str]
