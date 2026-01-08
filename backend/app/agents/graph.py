from typing import Literal, List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings
from app.agents.state import AgentState
from app.agents.tools import retrieve_tool, arxiv_tool, python_interpreter_tool, summarize_section_tool, web_search_tool
from app.agents.graders import retrieval_grader, hallucination_grader, answer_grader

# --- LLM & Tools ---
tools = [retrieve_tool, arxiv_tool, python_interpreter_tool, summarize_section_tool, web_search_tool]
llm = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0)
llm_with_tools = llm.bind_tools(tools)

# --- Nodes ---

def agent(state: AgentState):
    """
    Invokes the agent model to generate a response or tool call.
    """
    print("---CALL AGENT---")
    messages = state["messages"]
    
    # System message if not present
    if not isinstance(messages[0], SystemMessage):
        sys_msg = SystemMessage(content="""You are a senior research assistant. 
Use your tools to answer questions. 
When providing an answer based on retrieved info, use inline citations like [1], [2].
Always verify your answers.""")
        messages = [sys_msg] + messages
        
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def grade_documents(state: AgentState):
    """
    Determines whether the retrieved documents are relevant to the question.
    """
    print("---CHECK DOCUMENT RELEVANCE---")
    messages = state["messages"]
    last_message = messages[-1]
    
    # Check if last message is a ToolMessage
    if not hasattr(last_message, "tool_call_id"):
        # This shouldn't happen in the current edge configuration but good safety
        return state
        
    question = messages[0].content
    docs = last_message.content # String content from valid tool
    
    # We might need to handle the case where content is a list of dicts (from our retrieve_tool)
    # LangGraph ToolNode serializes it to a string usually.
    # Our retrieve_tool returns a list of dicts. 
    
    # Simplification: The tool output might be a JSON string repr of the list.
    # We will assume "documents" are relevant if at least one passes the grader.
    
    # Ideally, we iterate over each doc.
    # For this MVP, let's treat the whole context as one block to grade or parse it.
    
    score = retrieval_grader.invoke({"question": question, "document": docs})
    grade = score.binary_score
    
    if grade == "yes":
        from langchain_core.documents import Document
        retrieved_doc = Document(page_content=docs, metadata={"source": "Retrieved Tool"})
        
        return {"is_relevant": True, "documents": [retrieved_doc]}
    else:
        print("---DECISION: DOCS NOT RELEVANT---")
        return {"is_relevant": False}

def generate(state: AgentState):
    """
    Generate answer
    """
    print("---GENERATE---")
    messages = state["messages"]
    
    # Logic to formulate answer based on conversation
    response = llm.invoke(messages)
    return {"messages": [response]}

# --- Conditional Logic ---

def should_continue(state: AgentState) -> Literal["tools", "grade_generation", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]
    
    if last_message.tool_calls:
        return "tools"
    
    # If no tool calls, it's an answer. Grade it.
    return "grade_generation"




def grade_generation_v_documents_and_question(state: AgentState):
    """
    Determines whether the generation is grounded in the document and answers question.
    """
    print("---CHECK HALLUCINATIONS---")
    question = state["messages"][0].content
    messages = state["messages"]
    last_message = messages[-1]
    generation = last_message.content
    
    # Get last tool message content as "facts"
    # Simplification: Find last ToolMessage
    docs = ""
    for msg in reversed(messages):
        if hasattr(msg, "tool_call_id"):
            docs = msg.content
            break
            
    # Grades
    hallucination_score = hallucination_grader.invoke({"documents": docs, "generation": generation})
    grade = hallucination_score.binary_score
    
    if grade == "yes":
        print("---DECISION: GENERATION IS GROUNDED---")
        # Check answer quality
        print("---CHECK ANSWER QUALITY---")
        answer_score = answer_grader.invoke({"question": question, "generation": generation})
        grade = answer_score.binary_score
        
        if grade == "yes":
             print("---DECISION: GENERATION ADDRESSES QUESTION---")
             return {"is_supported": True}
        else:
             print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
             return {"is_supported": False, "retry_count": state.get("retry_count", 0) + 1}
    else:
         print("---DECISION: GENERATION IS HALLUCINATION---")
         return {"is_supported": False, "retry_count": state.get("retry_count", 0) + 1}

def grade_generation_decision(state: AgentState) -> Literal["__end__", "agent"]:
    """
    Determines if generation is valid or needs retry.
    """
    print("---CHECK GENERATION DECISION---")
    if state.get("is_supported", True): 
       return "__end__"
    
    if state.get("retry_count", 0) > 5:
        print("---MAX RETRIES REACHED---")
        return "__end__"
        
    return "agent"

def rewrite(state: AgentState):
    """
    Transform the query to produce a better question.
    """
    print("---TRANSFORM QUERY---")
    messages = state["messages"]
    question = messages[0].content
    
    msg = [HumanMessage(content=f"Look at the input and try to reason about the underlying semantic intent / meaning. \n Here is the initial question: \n\n {question} \n Formulate an improved question.")]
    
    # Grader LLM can be used or the main agent model
    response = llm.invoke(msg)
    
    return {"messages": [HumanMessage(content=response.content)]}

def check_relevance(state: AgentState) -> Literal["agent", "rewrite"]:
    """
    Determines if retrieved documents are relevant.
    """
    print("---CHECK RELEVANCE---")
    if state.get("is_relevant", False):
        print("---DECISION: RELEVANT -> AGENT---")
        return "agent"
    else:
        print("---DECISION: NOT RELEVANT -> REWRITE---")
        return "rewrite"

# --- Planner ---
from pydantic import BaseModel, Field

class Plan(BaseModel):
    """Plan to follow for answering the user's request"""
    steps: List[str] = Field(description="different steps to follow, should be in sorted order")

structured_llm_planner = llm.with_structured_output(Plan)

planner_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "For the given objective, come up with a simple step by step plan. \n This plan should involve using tools like retrieve_tool (for searching), summarize_section_tool (for specific sections), or python_interpreter_tool (for math). \n Be concise."),
        ("human", "{objective}")
    ]
)

planner = planner_prompt | structured_llm_planner

def plan_node(state: AgentState):
    print("---PLANNING---")
    messages = state["messages"]
    question = messages[0].content
    
    # If we already have a plan (e.g. from retry), maybe we keep it? 
    # For now, simplistic approach: always plan at start.
    
    plan_result = planner.invoke({"objective": question})
    
    # Create a system message with the plan to guide the agent
    steps_str = "\n".join([f"{i+1}. {step}" for i, step in enumerate(plan_result.steps)])
    sys_msg = SystemMessage(content=f"You are a helpful research assistant. \n Here is your plan: \n {steps_str} \n\n Follow this plan to answer the user's question. \n Use your tools.")
    
    # We update messages to include this guidance
    return {"plan": plan_result.steps, "messages": [sys_msg]}

# --- Graph ---
workflow = StateGraph(AgentState)

# Define nodes
workflow.add_node("planner", plan_node)
workflow.add_node("agent", agent)
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("grade_generation", grade_generation_v_documents_and_question)
workflow.add_node("rewrite", rewrite)

# Define edges
# Start with planner
workflow.add_edge(START, "planner")
workflow.add_edge("planner", "agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "grade_generation": "grade_generation",
        "__end__": END,
    },
)

workflow.add_edge("tools", "grade_documents")

workflow.add_conditional_edges(
    "grade_documents",
    check_relevance,
    {
        "agent": "agent",
        "rewrite": "rewrite",
    },
)

workflow.add_edge("rewrite", "agent")

workflow.add_conditional_edges(
    "grade_generation",
    grade_generation_decision,
    {
        "__end__": END,
        "agent": "agent",
    }
)

# Compile
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
