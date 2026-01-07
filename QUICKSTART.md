# Quick Start Guide

Get your Research RAG Assistant running in 5 minutes.

## Prerequisites

- Python 3.10+
- Node.js 18+
- OpenAI API key

## Step 1: Backend Setup

```bash
# Navigate to backend
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-...
```

Start the backend server:
```bash
uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## Step 2: Frontend Setup

In a new terminal:

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

You should see:
```
▲ Next.js 16.0.10
- Local:        http://localhost:3000
```

## Step 3: Use the System

1. Open http://localhost:3000 in your browser
2. Click "Upload PDF" in the sidebar
3. Upload a research paper (PDF format)
4. Wait for processing (you'll see chunk count)
5. Ask questions in the chat panel
6. View citations and knowledge graph in the context panel

## Example Questions

- "What is the main contribution of this paper?"
- "Explain the methodology used in this research"
- "What are the key findings and results?"
- "How does this approach compare to previous work?"

## Architecture Overview

```
Frontend (localhost:3000)
    ↓ API calls
Backend (localhost:8000)
    ↓ stores embeddings
ChromaDB (./backend/chroma_db)
    ↓ generates answers
OpenAI GPT-4o-mini
```

## Troubleshooting

**Backend won't start:**
- Check Python version: `python --version` (need 3.10+)
- Verify all dependencies installed: `pip list`
- Check OpenAI API key in `.env`

**Frontend won't start:**
- Check Node version: `node --version` (need 18+)
- Delete `node_modules` and run `npm install` again

**Can't upload PDFs:**
- Ensure backend is running on port 8000
- Check browser console for errors
- Verify `backend/uploaded_papers` directory exists

**No answers generated:**
- Verify OpenAI API key is valid
- Check backend logs for errors
- Ensure ChromaDB directory has write permissions

## Next Steps

- Review `backend/README.md` for API documentation
- Customize chunking parameters in `backend/app/core/config.py`
- Adjust UI colors in `app/globals.css`
- Add more papers and build your research knowledge base

## Production Deployment

For production use:
- Use a managed vector database (Pinecone, Weaviate)
- Add authentication and user management
- Implement rate limiting
- Use a production WSGI server (Gunicorn)
- Deploy frontend to Vercel
- Set up proper logging and monitoring
