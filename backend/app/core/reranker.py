from sentence_transformers import CrossEncoder
from typing import List, Dict, Tuple
from app.core.config import settings

class Reranker:
    """Cross-encoder reranking for retrieved chunks"""
    
    def __init__(self):
        self.model = CrossEncoder(settings.RERANKER_MODEL)
    
    def rerank(self, query: str, chunks: List[Dict], top_k: int = 5) -> List[Tuple[Dict, float]]:
        """
        Rerank chunks using cross-encoder
        
        Returns:
            List of (chunk, score) tuples, sorted by score
        """
        # Prepare pairs for cross-encoder
        pairs = [(query, chunk["text"]) for chunk in chunks]
        
        # Get scores
        scores = self.model.predict(pairs)
        
        # Normalize scores to 0-1 range (confidence)
        min_score = min(scores)
        max_score = max(scores)
        normalized_scores = [
            float((score - min_score) / (max_score - min_score)) if max_score > min_score else 0.5
            for score in scores
        ]
        
        # Combine chunks with scores
        chunk_scores = list(zip(chunks, normalized_scores))
        
        # Sort by score descending
        chunk_scores.sort(key=lambda x: x[1], reverse=True)
        
        return chunk_scores[:top_k]

# Singleton instance
reranker = Reranker()
