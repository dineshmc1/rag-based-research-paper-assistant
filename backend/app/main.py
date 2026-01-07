from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import ingest, chat, papers, graph
from app.core.config import settings

app = FastAPI(title="Research RAG Assistant", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router, prefix="/api/ingest", tags=["ingest"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(papers.router, prefix="/api/papers", tags=["papers"])
app.include_router(graph.router, prefix="/api/graph", tags=["graph"])

@app.get("/")
async def root():
    return {"message": "Research RAG Assistant API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
