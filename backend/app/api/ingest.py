from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict
import os
import shutil
from app.core.pdf_parser import PDFParser
from app.core.chunking import SemanticChunker
from app.core.embeddings import embedding_model
from app.db.chroma import chroma_db
from app.core.config import settings
import uuid

router = APIRouter()

UPLOAD_DIR = "./uploaded_papers"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_paper(file: UploadFile = File(...)) -> Dict:
    """
    Upload and process a research PDF
    
    Returns paper_id and processing stats
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Generate paper ID
    paper_id = str(uuid.uuid4())
    
    # Save file
    file_path = os.path.join(UPLOAD_DIR, f"{paper_id}.pdf")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Parse PDF
        pages_data = PDFParser.parse_pdf(file_path)
        
        # Chunk text
        chunker = SemanticChunker(
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP
        )
        
        all_chunks = []
        for page_data in pages_data:
            # Skip references section
            if PDFParser.should_skip_section(page_data["section"]):
                continue
            
            chunks = chunker.chunk_text(
                text=page_data["text"],
                page_number=page_data["page_number"],
                section=page_data["section"],
                paper_id=paper_id
            )
            all_chunks.extend(chunks)
        
        # Generate embeddings
        chunk_texts = [chunk["text"] for chunk in all_chunks]
        embeddings = embedding_model.embed_batch(chunk_texts)
        
        # Store in ChromaDB
        chroma_db.add_chunks(all_chunks, embeddings)
        
        return {
            "paper_id": paper_id,
            "filename": file.filename,
            "total_pages": len(pages_data),
            "total_chunks": len(all_chunks),
            "status": "success"
        }
        
    except Exception as e:
        # Clean up on failure
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.delete("/paper/{paper_id}")
async def delete_paper(paper_id: str) -> Dict:
    """Delete a paper and its chunks"""
    try:
        # Delete from ChromaDB
        chroma_db.delete_paper(paper_id)
        
        # Delete file
        file_path = os.path.join(UPLOAD_DIR, f"{paper_id}.pdf")
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {"status": "deleted", "paper_id": paper_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")
