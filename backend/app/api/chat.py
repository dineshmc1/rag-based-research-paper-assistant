from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, List
from app.core.query_expansion import query_expander
from app.core.embeddings import embedding_model
from app.db.chroma import chroma_db
from app.core.reranker import reranker
from app.core.answer_synthesis import answer_synthesizer
from app.core.config import settings
from dotenv import load_dotenv
load_dotenv()
router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    paper_ids: List[str] = []  # List of paper IDs to search
    include_reasoning: bool = False
    execution_mode: str = "text" # "text" or "python"

class ChatResponse(BaseModel):
    answer: str
    citations: List[Dict]
    retrieved_chunks: List[Dict]
    concepts: List[str]
    artifacts: Optional[List[Dict]] = None
    reasoning: Optional[Dict] = None

@router.post("/query", response_model=ChatResponse)
async def query_papers(request: ChatRequest) -> ChatResponse:
    """
    Agentic RAG query using LangGraph
    """
    try:
        from app.agents.graph import app as agent_app
        from langchain_core.messages import HumanMessage
        
        # Initial state
        initial_state = {
            "messages": [HumanMessage(content=request.query)],
            "paper_ids": request.paper_ids,  # Papers to search
            "is_relevant": True,
            "is_supported": True,
            "documents": [],
            "reasoning_trace": [],
            "citations": [],
            "artifacts": [],
            "execution_mode": request.execution_mode,
            "execution_status": "started",
            "retry_count": 0,
            "plan": []
        }
        
        # Invoke agent with increased recursion limit
        config = {
            "configurable": {"thread_id": "1"},  # TODO: Use session ID
            "recursion_limit": 50  # Prevent GraphRecursionError
        }
        final_state = await agent_app.ainvoke(initial_state, config=config)
        
        # Extract answer - find the last AIMessage with actual content
        messages = final_state["messages"]
        answer = ""
        
        # Search backwards for the last AI message with content
        for msg in reversed(messages):
            # Check if it's an AI message (not a tool message, not human)
            if hasattr(msg, 'content') and msg.content:
                msg_type = type(msg).__name__
                # AIMessage or similar - has content and is not a ToolMessage or HumanMessage
                if 'AI' in msg_type or msg_type == 'AIMessage':
                    answer = msg.content
                    break
        
        # Fallback: if no AIMessage found, use the last message with content
        if not answer:
            for msg in reversed(messages):
                if hasattr(msg, 'content') and msg.content and len(msg.content) > 10:
                    answer = msg.content
                    break
        
        # Ultimate fallback
        if not answer:
            answer = "I apologize, but I was unable to generate a complete response. Please try rephrasing your question."
            
        state_docs = final_state.get("documents", [])
        state_artifacts = final_state.get("artifacts", [])
        citations = []
        retrieved_chunks = []

        # ... (citation processing) ...
        for i, doc in enumerate(state_docs):
            # Create the citation for the frontend
            # Ensure safe type conversion for confidence
            try:
                score = float(doc.metadata.get("score", 0.0))
            except (ValueError, TypeError):
                score = 0.0
            
            # Get page number - use page_number key, fallback to parsing source
            page = doc.metadata.get("page_number")
            if page is None:
                # Try to parse from source string "Page X - Section Y"
                source_str = doc.metadata.get("source", "")
                if "Page " in source_str:
                    try:
                        page = int(source_str.split("Page ")[1].split(" -")[0])
                    except (ValueError, IndexError):
                        page = None
            
            # Get section
            section = doc.metadata.get("section")
            if not section:
                source_str = doc.metadata.get("source", "")
                if "Section " in source_str:
                    section = source_str.split("Section ")[-1]
                    
            citation = {
                "paper": doc.metadata.get("paper_id") or "unknown",
                "page": page,
                "chunk_id": doc.metadata.get("chunk_id") or f"chunk_{i}",
                "confidence": score,
                "section": section,
                "content": doc.page_content # Keep content just in case
            }
            citations.append(citation)
            
            # Create the chunk for the UI
            retrieved_chunks.append({
                "text": doc.page_content,
                "index": i + 1
            })
        
        concepts = extract_concepts(answer)
        
        # Append artifacts to answer if present (for backward compatibility / easy rendering)
        if state_artifacts:
            for art in state_artifacts:
                if art["type"] == "image":
                    answer += f"\n\n![{art['name']}]({art['path']})"
        
        return ChatResponse(
            answer=answer,
            citations=citations, 
            retrieved_chunks=retrieved_chunks,
            concepts=concepts,
            artifacts=state_artifacts,
            reasoning={"steps": final_state.get("plan", [])}
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

def extract_concepts(text: str) -> List[str]:
    """Simple concept extraction from answer text"""
    # This is a placeholder - could use NER or keyword extraction
    import re
    
    # Extract capitalized phrases and technical terms
    words = text.split()
    concepts = []
    
    for word in words:
        # Remove punctuation
        clean_word = re.sub(r'[^\w\s-]', '', word)
        # Add if it looks like a concept (capitalized, technical term, etc.)
        if len(clean_word) > 3 and (clean_word[0].isupper() or '-' in clean_word):
            if clean_word not in concepts:
                concepts.append(clean_word)
    
    return concepts[:10]  # Limit to top 10
