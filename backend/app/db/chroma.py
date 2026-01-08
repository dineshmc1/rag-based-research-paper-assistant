import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Optional
from app.core.config import settings
from app.core.embeddings import embedding_model
import os

class ChromaDBManager:
    """Manages ChromaDB vector store"""
    
    def __init__(self):
        # Create persist directory if it doesn't exist
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_chunks(self, chunks: List[Dict], embeddings: List[List[float]]):
        """Add chunks with embeddings to ChromaDB"""
        ids = [chunk["chunk_id"] for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [
            {
                "page_number": chunk["page_number"],
                "section": chunk["section"],
                "paper_id": chunk["paper_id"]
            }
            for chunk in chunks
        ]
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
    
    def query(self, query_embedding: List[float], top_k: int = 20, paper_id: Optional[str] = None) -> List[Dict]:
        """Query ChromaDB for similar chunks"""
        where_filter = {"paper_id": paper_id} if paper_id else None
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter
        )
        
        # Format results
        chunks = []
        for i in range(len(results["ids"][0])):
            chunks.append({
                "chunk_id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "page_number": results["metadatas"][0][i]["page_number"],
                "section": results["metadatas"][0][i]["section"],
                "paper_id": results["metadatas"][0][i]["paper_id"],
                "distance": results["distances"][0][i] if "distances" in results else 0
            })
        
        return chunks
    
    def get_paper_chunks(self, paper_id: str) -> List[Dict]:
        """Get all chunks for a specific paper"""
        results = self.collection.get(
            where={"paper_id": paper_id}
        )
        
        chunks = []
        for i in range(len(results["ids"])):
            chunks.append({
                "chunk_id": results["ids"][i],
                "text": results["documents"][i],
                "page_number": results["metadatas"][i]["page_number"],
                "section": results["metadatas"][i]["section"],
                "paper_id": results["metadatas"][i]["paper_id"]
            })
        
        return chunks
    
    def delete_paper(self, paper_id: str):
        """Delete all chunks for a paper"""
        self.collection.delete(
            where={"paper_id": paper_id}
        )

    
    def query_section(self, section_name: str, paper_id: Optional[str] = None) -> List[Dict]:
        """Query ChromaDB for all chunks in a specific section."""
        where_filter = {"section": section_name}
        if paper_id:
            where_filter = {"$and": [{"section": section_name}, {"paper_id": paper_id}]}
            
        # We want all chunks in that section, so we use get() instead of query()
        results = self.collection.get(
            where=where_filter
        )
        
        chunks = []
        for i in range(len(results["ids"])):
            chunks.append({
                "chunk_id": results["ids"][i],
                "text": results["documents"][i],
                "page_number": results["metadatas"][i]["page_number"],
                "section": results["metadatas"][i]["section"],
                "paper_id": results["metadatas"][i]["paper_id"]
            })
        
        return chunks

# Singleton instance
chroma_db = ChromaDBManager()
