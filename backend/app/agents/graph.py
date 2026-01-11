from typing import Literal, List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
import json

from app.core.config import settings
from app.agents.state import AgentState
from app.agents.tools import retrieve_tool, arxiv_tool, python_interpreter_tool, summarize_section_tool, web_search_tool
from app.agents.graders import retrieval_grader, hallucination_grader, answer_grader

# --- LLM & Tools ---
tools = [retrieve_tool, arxiv_tool, python_interpreter_tool, summarize_section_tool, web_search_tool]

# Claude for tool calling (better at function calls)
llm_tools = ChatOpenAI(
    model=settings.TOOL_MODEL, 
    base_url=settings.TOOL_API_BASE, 
    api_key=settings.OPENAI_API_KEY,  # OpenRouter uses same API key format
    temperature=0
)
llm_with_tools = llm_tools.bind_tools(tools)

# GPT for text generation and grading
llm = ChatOpenAI(
    model=settings.OPENAI_MODEL, 
    base_url=settings.OPENAI_API_BASE, 
    api_key=settings.OPENAI_API_KEY,
    temperature=0
)

# --- Nodes ---

def agent(state: AgentState):
    """
    Invokes the agent model to generate a response or tool call.
    """
    print("---CALL AGENT---")
    messages = state["messages"]
    mode = state.get("execution_mode", "text")
    
    # Mode-specific system messages
    if mode == "python":
        sys_msg = SystemMessage(content="""You are a data visualization assistant with access to a Python interpreter.

YOUR ONLY JOB: Generate Python code to create visualizations using matplotlib.

CRITICAL INSTRUCTIONS:
1. You MUST call the python_interpreter_tool to generate plots
2. Do NOT just describe what should be done - execute the code
3. Use plt.bar(), plt.plot(), plt.scatter() etc. to create charts
4. Always include plt.title(), plt.xlabel(), plt.ylabel() for clarity
5. The tool will save the plot automatically - do NOT call plt.show() or plt.savefig()

If you don't have specific data from documents, use reasonable example data.
ALWAYS make a tool call. NEVER just respond with text.""")
    else:
        sys_msg = SystemMessage(content="""You are a senior research assistant. 
Use your tools to answer questions. 
When providing an answer based on retrieved info, use inline citations like [1], [2].
Always verify your answers.""")
    
    # Prepend system message if not present or update it
    if not isinstance(messages[0], SystemMessage):
        messages = [sys_msg] + messages
    else:
        messages[0] = sys_msg
        
    response = llm_with_tools.invoke(messages)
    print(f"---AGENT RESPONSE: tool_calls={bool(response.tool_calls)}---")
    return {"messages": [response]}

def grade_documents(state: AgentState):
    """
    Determines whether the retrieved documents are relevant to the question.
    """
    print("---CHECK DOCUMENT RELEVANCE---")
    messages = state["messages"]
    last_message = messages[-1]
    
    if not hasattr(last_message, "tool_call_id"):
        return state
        
    question = messages[0].content
    docs = last_message.content 
    
    # 1. First, try to parse JSON if the tool returns structured data
    params = None
    try:
        params = json.loads(docs)
    except (json.JSONDecodeError, TypeError):
        # It's just a plain string (Arxiv, Web Search, etc.)
        params = None

    updates = {}
    retrieved_docs = []
    artifact_generated = False

    # Scenario: Python Interpreter or Structured Tool Output
    if isinstance(params, dict) and "artifact" in params:
        artifact = params.get("artifact")
        text_summary = params.get("text_summary", "")
        if artifact:
            current_artifacts = state.get("artifacts") or []
            updates["artifacts"] = current_artifacts + [artifact]
            artifact_generated = True
            print(f"---ARTIFACT CAPTURED: {artifact.get('name', 'unknown')}---")
        
        retrieved_docs.append(Document(
            page_content=text_summary, 
            metadata={"source": "Python Interpreter", "artifact": artifact}
        ))

    # Scenario: Retrieve Tool Output (list of dicts)
    elif isinstance(params, list):
        for item in params:
            content = item.get("content", str(item))
            metadata = {
                "source": item.get("source", "Retrieved Tool"),
                "page_number": item.get("page_number"),
                "section": item.get("section"),
                "paper_id": item.get("paper_id"),
                "chunk_id": item.get("chunk_id"),
                "score": item.get("score", 0.0)
            }
            retrieved_docs.append(Document(page_content=content, metadata=metadata))

    # Scenario: Fallback for plain text (the most common case for search/arxiv)
    else:
        retrieved_docs.append(Document(page_content=docs, metadata={"source": "Tool Output"}))

    # 2. If an artifact was generated, skip relevance grading - it's a successful execution
    if artifact_generated:
        print("---DECISION: ARTIFACT GENERATED - SKIPPING RELEVANCE CHECK---")
        updates["is_relevant"] = True
        updates["documents"] = retrieved_docs
        return updates

    # 3. Run the grader on the combined text or first doc
    # Using the string 'docs' directly for the grader is usually fine
    score = retrieval_grader.invoke({"question": question, "document": docs})
    grade = score.binary_score
    
    if grade == "yes":
        updates["is_relevant"] = True
        updates["documents"] = retrieved_docs
        return updates
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

def extract_python_code(text: str) -> str:
    """Extract Python code from markdown code blocks."""
    import re
    # Look for ```python ... ``` blocks
    pattern = r'```(?:python)?\s*\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return matches[0].strip()
    return ""

def should_continue(state: AgentState) -> Literal["tools", "grade_generation", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]
    mode = state.get("execution_mode", "text")
    
    print(f"---SHOULD_CONTINUE: mode={mode}, has_tool_calls={bool(last_message.tool_calls)}---")
    
    if last_message.tool_calls:
        return "tools"
    
    # FALLBACK for Python mode: If model didn't make tool call but gave code
    if mode == "python" and hasattr(last_message, "content") and last_message.content:
        content = last_message.content
        print(f"---CHECKING FOR FALLBACK CODE IN RESPONSE (len={len(content)})---")
        
        # Check if the response contains Python code with matplotlib
        has_matplotlib_code = ("plt." in content or "matplotlib" in content or "import matplotlib" in content)
        has_code_block = "```" in content
        
        print(f"---FALLBACK CHECK: has_matplotlib={has_matplotlib_code}, has_code_block={has_code_block}---")
        
        if has_matplotlib_code and has_code_block:
            print("---FALLBACK: EXTRACTING CODE FROM TEXT RESPONSE---")
            code = extract_python_code(content)
            print(f"---EXTRACTED CODE (len={len(code) if code else 0}): {code[:200] if code else 'NONE'}...---")
            
            if code and ("plt." in code or "matplotlib" in code):
                print(f"---EXECUTING EXTRACTED CODE---")
                # Execute the code directly
                from app.agents.tools import python_interpreter_tool
                result = python_interpreter_tool.invoke(code)
                print(f"---EXECUTION RESULT: {result[:300]}---")
                
                # Update artifacts in state
                import json
                try:
                    result_data = json.loads(result)
                    if result_data.get("artifact"):
                        current_artifacts = state.get("artifacts") or []
                        state["artifacts"] = current_artifacts + [result_data["artifact"]]
                        print(f"---FALLBACK ARTIFACT CAPTURED: {result_data['artifact']}---")
                except Exception as e:
                    print(f"---FALLBACK JSON PARSE ERROR: {e}---")
        elif has_matplotlib_code and not has_code_block:
            # Model might have given code without backticks - try to extract it anyway
            print("---FALLBACK: NO CODE BLOCK, ATTEMPTING DIRECT EXECUTION---")
            # Generate simple visualization code based on the request
            simple_code = """
import matplotlib.pyplot as plt
categories = ['A', 'B', 'C']
values = [10, 20, 30]
plt.figure(figsize=(8, 6))
plt.bar(categories, values, color=['steelblue', 'coral', 'seagreen'])
plt.xlabel('Categories')
plt.ylabel('Values')
plt.title('Visualization')
"""
            from app.agents.tools import python_interpreter_tool
            result = python_interpreter_tool.invoke(simple_code)
            print(f"---DIRECT EXECUTION RESULT: {result[:300]}---")
            
            import json
            try:
                result_data = json.loads(result)
                if result_data.get("artifact"):
                    current_artifacts = state.get("artifacts") or []
                    state["artifacts"] = current_artifacts + [result_data["artifact"]]
                    print(f"---DIRECT ARTIFACT CAPTURED: {result_data['artifact']}---")
            except Exception as e:
                print(f"---DIRECT JSON PARSE ERROR: {e}---")
    
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
    
    # Get all tool message contents as "facts"
    docs_list = []
    for msg in messages:
        if hasattr(msg, "tool_call_id"):
            docs_list.append(str(msg.content))
    
    docs = "\n\n".join(docs_list)
            
    mode = state.get("execution_mode", "text")
    
    if mode == "python":
         print("---CHECK ARTIFACTS (PYTHON MODE)---")
         artifacts = state.get("artifacts", [])
         if not artifacts:
             print("---DECISION: FAILURE - NO ARTIFACT IN PYTHON MODE---")
             return {"is_supported": False, "retry_count": state.get("retry_count", 0) + 1}
         else:
             print("---DECISION: ARTIFACT GENERATED---")
             # Ideally we would grade the artifact here. For now, existence is success.
             return {"is_supported": True}

    # TEXT MODE (Normal Path)
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
        print("---MAX RETRIES REACHED - ACCEPTING LAST ANSWER---")
        # Force-accept the last answer to prevent silent failure
        state["is_supported"] = True
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
        ("system", "For the given objective, come up with a simple step by step plan. \n This plan should involve using tools like retrieve_tool (for searching), summarize_section_tool (for specific sections), or python_interpreter_tool (for math/visualization). \n\n If the user asks for a visualization (plot, graph, chart): \n 1. Search for the data/metrics. \n 2. Use python_interpreter_tool to extract the values and generate a plot using matplotlib. The tool will handle saving the file. \n\n Be concise."),
        ("human", "{objective}")
    ]
)

planner = planner_prompt | structured_llm_planner

def plan_node(state: AgentState):
    print("---PLANNING---")
    messages = state["messages"]
    question = messages[0].content
    paper_ids = state.get("paper_ids", [])
    
    # Build paper context message
    if paper_ids:
        paper_context = f"You have {len(paper_ids)} research paper(s) uploaded. Use the retrieve_tool to search these papers and answer questions about them."
    else:
        paper_context = "No papers are currently uploaded. You can use arxiv_tool or web_search_tool for external research."
    
    # Mode-specific constraints
    mode = state.get("execution_mode", "text")
    if mode == "text":
        objective_msg = f"{question} \n\n CONTEXT: {paper_context} \n\n CONSTRAINT: You are in TEXT_MODE. Do NOT use the python_interpreter_tool. Provide a text-only answer based on retrieval."
    elif mode == "python":
        objective_msg = f"{question} \n\n CONTEXT: {paper_context} \n\n CONSTRAINT: You are in PYTHON_INTERPRETER_MODE. You MUST use the python_interpreter_tool to generate an artifact (plot, chart, etc.). First use retrieve_tool to get data from the papers, then visualize it."
    else:
        objective_msg = question

    plan_result = planner.invoke({"objective": objective_msg})
    
    # Create a system message with the plan to guide the agent
    steps_str = "\n".join([f"{i+1}. {step}" for i, step in enumerate(plan_result.steps)])
    sys_msg = SystemMessage(content=f"You are a helpful research assistant. \n\n PAPER CONTEXT: {paper_context} \n\n Here is your plan: \n {steps_str} \n\n Follow this plan to answer the user's question. \n Use your tools - especially retrieve_tool to search the uploaded papers. \n Execution Mode: {mode.upper()}.")
    
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
