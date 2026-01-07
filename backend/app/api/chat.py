from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, List
from app.core.query_expansion import query_expander
from app.core.embeddings import embedding_model
from app.db.chroma import chroma_db
from app.core.reranker import reranker
from app.core.answer_synthesis import answer_synthesizer
from app.core.config import settings

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    paper_id: Optional[str] = None
    include_reasoning: bool = False

class ChatResponse(BaseModel):
    answer: str
    citations: List[Dict]
    retrieved_chunks: List[Dict]
    concepts: List[str]
    reasoning: Optional[Dict] = None

@router.post("/query", response_model=ChatResponse)
async def query_papers(request: ChatRequest) -> ChatResponse:
    """
    Deep RAG query with expansion and reranking
    
    Process:
    1. Query expansion (generate variants)
    2. Parallel vector search
    3. Cross-encoder reranking
    4. Answer synthesis with citations
    5. Concept extraction
    """
    try:
        reasoning_steps = {} if request.include_reasoning else None
        
        # Step 1: Query expansion
        query_variants = await query_expander.expand_query(
            request.query,
            num_variants=settings.NUM_QUERY_VARIANTS
        )
        
        if reasoning_steps is not None:
            reasoning_steps["query_variants"] = query_variants
        
        # Step 2: Parallel retrieval for all variants
        all_chunks = []
        seen_chunk_ids = set()
        
        for variant in query_variants:
            # Embed query variant
            query_embedding = embedding_model.embed_text(variant)
            
            # Retrieve chunks
            chunks = chroma_db.query(
                query_embedding=query_embedding,
                top_k=settings.TOP_K_RETRIEVAL,
                paper_id=request.paper_id
            )
            
            # Deduplicate
            for chunk in chunks:
                if chunk["chunk_id"] not in seen_chunk_ids:
                    all_chunks.append(chunk)
                    seen_chunk_ids.add(chunk["chunk_id"])
        
        if reasoning_steps is not None:
            reasoning_steps["total_retrieved"] = len(all_chunks)
        
        if not all_chunks:
            return ChatResponse(
                answer="I couldn't find relevant information in the papers to answer this question.",
                citations=[],
                retrieved_chunks=[],
                concepts=[],
                reasoning=reasoning_steps
            )
        
        # Step 3: Rerank with cross-encoder
        reranked_chunks = reranker.rerank(
            query=request.query,
            chunks=all_chunks,
            top_k=settings.TOP_K_RERANKED
        )
        
        if reasoning_steps is not None:
            reasoning_steps["reranked_count"] = len(reranked_chunks)
            reasoning_steps["top_scores"] = [score for _, score in reranked_chunks[:3]]
        
        # Step 4: Synthesize answer
        result = await answer_synthesizer.synthesize(
            query=request.query,
            chunks_with_scores=reranked_chunks
        )
        
        # Step 5: Extract concepts (simple keyword extraction)
        concepts = extract_concepts(result["answer"])
        
        return ChatResponse(
            answer=result["answer"],
            citations=result["citations"],
            retrieved_chunks=result["retrieved_chunks"],
            concepts=concepts,
            reasoning=reasoning_steps
        )
        
    except Exception as e:
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
