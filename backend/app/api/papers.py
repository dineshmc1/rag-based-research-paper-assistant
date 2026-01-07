from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import List, Dict
import os
from app.db.chroma import chroma_db

router = APIRouter()

UPLOAD_DIR = "./uploaded_papers"

@router.get("/list")
async def list_papers() -> List[Dict]:
    """List all uploaded papers"""
    try:
        papers = []
        
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                if filename.endswith('.pdf'):
                    paper_id = filename.replace('.pdf', '')
                    
                    # Get chunk count from ChromaDB
                    chunks = chroma_db.get_paper_chunks(paper_id)
                    
                    papers.append({
                        "paper_id": paper_id,
                        "filename": filename,
                        "chunks_count": len(chunks)
                    })
        
        return papers
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list papers: {str(e)}")

@router.get("/{paper_id}/download")
async def download_paper(paper_id: str):
    """Download a paper PDF"""
    file_path = os.path.join(UPLOAD_DIR, f"{paper_id}.pdf")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=f"{paper_id}.pdf"
    )

@router.get("/{paper_id}/chunks")
async def get_paper_chunks(paper_id: str) -> List[Dict]:
    """Get all chunks for a paper"""
    try:
        chunks = chroma_db.get_paper_chunks(paper_id)
        return chunks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chunks: {str(e)}")
