from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from app.db.chroma import chroma_db
from app.core.reranker import reranker
from app.core.embeddings import embedding_model
from app.core.config import settings
import arxiv

@tool
def retrieve_tool(query: str, paper_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve relevant sections from the uploaded research papers.
    Use this tool when you need to answer a question based on the document context.
    
    Args:
        query: The search query string.
        paper_id: Optional UUID of a specific paper to restrict search to.
    """
    print(f"---RETRIEVING: {query} (paper_id={paper_id})---")
    
    # 1. Embed query
    query_embedding = embedding_model.embed_text(query)
    
    # 2. Retrieve from Chroma
    chunks = chroma_db.query(
        query_embedding=query_embedding,
        top_k=settings.TOP_K_RETRIEVAL,
        paper_id=paper_id
    )
    
    if not chunks:
        return []

    # 3. Rerank
    reranked_chunks = reranker.rerank(
        query=query,
        chunks=chunks,
        top_k=settings.TOP_K_RERANKED
    )
    
    # Format for agent
    results = []
    for chunk, score in reranked_chunks:
        results.append({
            "content": chunk["text"],
            "source": f"Page {chunk['page_number']} - Section {chunk['section']}",
            "paper_id": chunk["paper_id"],
            "score": score,
            "chunk_id": chunk["chunk_id"]
        })
        
    return results

@tool
def arxiv_tool(query: str) -> List[Dict[str, Any]]:
    """
    Search for research papers on arXiv.
    Use this tool ONLY when you need to find external, state-of-the-art, or recent papers
    that are NOT in the uploaded documents.
    
    Args:
        query: The search query.
    """
    print(f"---ARXIV SEARCH: {query}---")
    
    search = arxiv.Search(
        query=query,
        max_results=3,
        sort_by=arxiv.SortCriterion.Relevance
    )
    
    results = []
    for result in search.results():
        results.append({
            "title": result.title,
            "summary": result.summary,
            "url": result.pdf_url,
            "published": str(result.published)
        })
        
    return results

@tool
def python_interpreter_tool(code: str) -> str:
    """
    Execute Python code for math, data analysis, or logic.
    Use this tool for ANY numerical calculation or statistical comparison.
    The code must be safe, pure Python. NO internet access.
    
    Args:
        code: valid python code string.
    """
    print(f"---EXECUTING CODE---")
    try:
        # Create a safe globals dictionary
        safe_globals = {"__builtins__": None, "pd": None, "np": None, "math": None}
        # We can enable math modules
        import math
        safe_globals["math"] = math
        
        # Capture output
        import sys
        from io import StringIO
        old_stdout = sys.stdout
        redirected_output = sys.output = StringIO()
        
        exec(code, safe_globals)
        
        sys.stdout = old_stdout
        return redirected_output.getvalue()
        
    except Exception as e:
        return f"Error executing code: {e}"

@tool
def summarize_section_tool(section_name: str, paper_id: Optional[str] = None) -> str:
    """
    Summarize a specific section of the research paper(s).
    Valid section names: 'Abstract', 'Introduction', 'Methods', 'Results', 'Discussion', 'Conclusion'.
    
    Args:
        section_name: The name of the section using standard capitalization.
        paper_id: Optional paper ID to restrict to.
    """
    print(f"---SUMMARIZING SECTION: {section_name}---")
    
    # 1. Get raw text chunks
    chunks = chroma_db.query_section(section_name=section_name, paper_id=paper_id)
    
    if not chunks:
        return f"No content found for section '{section_name}'."
        
    # 2. Concatenate text (limit to fit context window if needed, naive join for now)
    context = "\n".join([c["text"] for c in chunks])
    
    # 3. Summarize using direct LLM call or new specialized prompt
    from app.core.config import settings
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage
    
    llm = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0)
    msg = HumanMessage(content=f"Synthesize and summarize the following content from the '{section_name}' section of a research paper. \n\n Content: \n {context[:20000]}...") # truncate for safety
    
    response = llm.invoke([msg])
    return response.content

@tool
def web_search_tool(query: str) -> str:
    """
    Search the web for information using Google Search (via Serper).
    Use this tool for:
    - Recent news or events (after knowledge cutoff)
    - Real-world impact or applications of research
    - Information NOT found in the uploaded papers or arXiv
    
    Args:
        query: The search query.
    """
    print(f"---WEB SEARCH: {query}---")
    from langchain_community.utilities import GoogleSerperAPIWrapper
    
    # Needs SERPER_API_KEY in env
    try:
        search = GoogleSerperAPIWrapper()
        return search.run(query)
    except Exception as e:
        return f"Web search failed. Did you add SERPER_API_KEY to .env? Error: {e}"
