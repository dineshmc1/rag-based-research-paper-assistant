from openai import OpenAI
from typing import List, Dict
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

class AnswerSynthesizer:
    """Synthesizes answers from retrieved chunks with citations"""
    
    @staticmethod
    async def synthesize(query: str, chunks_with_scores: List[tuple]) -> Dict:
        """
        Generate grounded answer with citations
        
        Args:
            query: User question
            chunks_with_scores: List of (chunk, confidence_score) tuples
        
        Returns:
            {answer, citations, reasoning}
        """
        # Prepare context from chunks
        context_parts = []
        for i, (chunk, score) in enumerate(chunks_with_scores):
            context_parts.append(
                f"[Source {i+1}] (Page {chunk['page_number']}, {chunk['section']})\n{chunk['text']}\n"
            )
        
        context = "\n".join(context_parts)
        
        prompt = f"""You are a research assistant analyzing academic papers. Answer the question based ONLY on the provided sources.

Sources:
{context}

Question: {query}

Instructions:
1. Provide a clear, comprehensive answer
2. Cite sources using [Source N] notation
3. If mathematical notation is needed, use LaTeX syntax
4. If the sources don't contain enough information, say so
5. Be precise and academic in tone

Answer:"""

        try:
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a precise research assistant who always cites sources."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Extract citations from answer
            citations = []
            for i, (chunk, score) in enumerate(chunks_with_scores):
                if f"[Source {i+1}]" in answer:
                    citations.append({
                        "paper": chunk["paper_id"],
                        "page": chunk["page_number"],
                        "chunk_id": chunk["chunk_id"],
                        "confidence": round(score, 2),
                        "section": chunk["section"]
                    })
            
            return {
                "answer": answer,
                "citations": citations,
                "retrieved_chunks": [
                    {
                        "text": chunk["text"],
                        "page": chunk["page_number"],
                        "section": chunk["section"],
                        "confidence": round(score, 2)
                    }
                    for chunk, score in chunks_with_scores
                ]
            }
            
        except Exception as e:
            print(f"Answer synthesis failed: {e}")
            return {
                "answer": "An error occurred while generating the answer.",
                "citations": [],
                "retrieved_chunks": []
            }

answer_synthesizer = AnswerSynthesizer()
