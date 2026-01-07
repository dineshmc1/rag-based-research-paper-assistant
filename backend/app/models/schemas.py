from pydantic import BaseModel
from typing import List, Optional

class ChunkMetadata(BaseModel):
    chunk_id: str
    page_number: int
    section: str
    paper_id: str

class Citation(BaseModel):
    paper: str
    page: int
    chunk_id: str
    confidence: float
    section: str

class RetrievedChunk(BaseModel):
    text: str
    page: int
    section: str
    confidence: float

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    retrieved_chunks: List[RetrievedChunk]
    concepts: List[str]
    reasoning: Optional[dict] = None
