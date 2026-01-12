from typing import TypedDict, Annotated, List, Dict, Any, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """The state of the agent in the LangGraph."""
    messages: Annotated[List[BaseMessage], add_messages]
    
    paper_ids: List[str]
    
    documents: List[Dict[str, Any]]
    
    is_relevant: bool
    is_supported: bool
    
    retry_count: int
    
    reasoning_trace: List[str]
    citations: List[Dict[str, Any]]
    
    artifacts: List[Dict[str, Any]]
    
    execution_mode: Literal["text", "python"]
    execution_status: str
    
    plan: List[str]
