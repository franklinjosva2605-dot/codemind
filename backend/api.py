"""
CodeMind — FastAPI REST API
Allows programmatic access to CodeMind indexing and querying.
"""

import os
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from backend.engine import index_files, answer_query, get_index_stats, reset_collection

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="CodeMind API",
    description="Enterprise Codebase Intelligence API powered by Gemini + ChromaDB",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Models ────────────────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    query: str
    chat_history: Optional[List[dict]] = []

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    chunks_used: int

class IndexResponse(BaseModel):
    total_chunks: int
    files: List[dict]

class StatsResponse(BaseModel):
    total_chunks: int
    sources: List[str]

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "app": "CodeMind",
        "version": "1.0.0",
        "status": "running",
        "description": "Enterprise Codebase Intelligence API"
    }

@app.get("/health", tags=["Health"])
def health():
    stats = get_index_stats()
    return {"status": "healthy", "indexed_chunks": stats["total_chunks"]}

@app.post("/index", response_model=IndexResponse, tags=["Indexing"])
async def index_endpoint(
    files: List[UploadFile] = File(...),
    reset: bool = False
):
    """Upload and index multiple files into the codebase knowledge base."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    files_data = []
    for f in files:
        content = await f.read()
        files_data.append({"name": f.filename, "bytes": content})

    try:
        result = index_files(files_data, reset=reset)
        return IndexResponse(
            total_chunks=result["total_chunks"],
            files=result["files"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def query_endpoint(request: QueryRequest):
    """Query the indexed codebase with a natural language question."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    stats = get_index_stats()
    if stats["total_chunks"] == 0:
        raise HTTPException(status_code=400, detail="No files indexed. Upload files first via /index")

    try:
        result = answer_query(
            query=request.query,
            chat_history=request.chat_history or []
        )
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            chunks_used=len(result["chunks"])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", response_model=StatsResponse, tags=["Index"])
def stats_endpoint():
    """Get current index statistics."""
    stats = get_index_stats()
    return StatsResponse(
        total_chunks=stats["total_chunks"],
        sources=stats["sources"]
    )

@app.delete("/index", tags=["Indexing"])
def reset_index():
    """Reset (clear) the entire index."""
    reset_collection()
    return {"message": "Index cleared successfully"}
