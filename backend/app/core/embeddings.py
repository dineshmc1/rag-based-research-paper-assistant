from sentence_transformers import SentenceTransformer
from typing import List
from app.core.config import settings

class EmbeddingModel:
    """Handles text embeddings"""
    
    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
    
    def embed_text(self, text: str) -> List[float]:
        """Embed single text"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts"""
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        return embeddings.tolist()

# Singleton instance
embedding_model = EmbeddingModel()
