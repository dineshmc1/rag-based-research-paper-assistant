from openai import OpenAI
from typing import List
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

class QueryExpander:
    """Expands user query into multiple variants for better retrieval"""
    
    @staticmethod
    async def expand_query(query: str, num_variants: int = 3) -> List[str]:
        """
        Generate query variants using LLM
        
        Returns:
            List of query variants including original
        """
        prompt = f"""You are a research assistant. Generate {num_variants} alternative phrasings of the following research question.
Each variant should capture the same intent but use different terminology.

Original Question: {query}

Provide {num_variants} variants, one per line, without numbering or extra formatting."""

        try:
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            variants_text = response.choices[0].message.content.strip()
            variants = [v.strip() for v in variants_text.split('\n') if v.strip()]
            
            # Always include original query
            all_queries = [query] + variants[:num_variants]
            return all_queries
            
        except Exception as e:
            print(f"Query expansion failed: {e}")
            return [query]  # Fallback to original

query_expander = QueryExpander()
