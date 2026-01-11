from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):

    anonymized_telemetry: bool = False  
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4.1-mini"
    
    # External Tools
    SERPER_API_KEY: Optional[str] = None
    
    # Embedding Model
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Reranker Model
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION: str = "research_papers"
    
    # Chunking params
    CHUNK_SIZE: int = 400
    CHUNK_OVERLAP: int = 50
    
    # Retrieval params
    TOP_K_RETRIEVAL: int = 20
    TOP_K_RERANKED: int = 5
    
    # Query expansion
    NUM_QUERY_VARIANTS: int = 3

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = Settings()
