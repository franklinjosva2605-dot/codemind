"""
CodeMind — Core RAG Engine
Handles file ingestion, chunking, embedding via Gemini, and ChromaDB storage.
"""

import os
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Any

import google.generativeai as genai
import chromadb
from chromadb.config import Settings
# Triggering a rebuild for chromadb
import pypdf

# ── Config ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
CHROMA_DIR     = "./chroma_store"
COLLECTION     = "codemind_index"
CHUNK_SIZE     = 800   # characters
CHUNK_OVERLAP  = 150

genai.configure(api_key=GEMINI_API_KEY)

# ── ChromaDB ──────────────────────────────────────────────────────────────────
def get_collection():
    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=Settings(anonymized_telemetry=False)
    )
    return client.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"}
    )

def reset_collection():
    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=Settings(anonymized_telemetry=False)
    )
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    return client.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"}
    )

# ── File Readers ──────────────────────────────────────────────────────────────
def read_pdf(file_bytes: bytes) -> str:
    import io
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def read_text(file_bytes: bytes) -> str:
    for enc in ["utf-8", "latin-1", "cp1252"]:
        try:
            return file_bytes.decode(enc)
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="replace")

def extract_text(filename: str, file_bytes: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return read_pdf(file_bytes)
    return read_text(file_bytes)

# ── Chunking ──────────────────────────────────────────────────────────────────
def chunk_text(text: str, source: str) -> List[Dict[str, str]]:
    """Split text into overlapping chunks."""
    chunks = []
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    start = 0
    idx = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end]
        if chunk.strip():
            chunks.append({
                "id":     hashlib.md5(f"{source}_{idx}".encode()).hexdigest(),
                "text":   chunk,
                "source": source,
                "chunk":  idx
            })
            idx += 1
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks

# ── Embedding ─────────────────────────────────────────────────────────────────
def embed_texts(texts: List[str]) -> List[List[float]]:
    """Batch embed using Gemini embedding model."""
    embeddings = []
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=batch,
            task_type="retrieval_document"
        )
        embeddings.extend(result["embedding"])
    return embeddings

# ── Indexing ──────────────────────────────────────────────────────────────────
def index_files(files: List[Dict[str, Any]], reset: bool = False) -> Dict[str, Any]:
    """
    Index a list of files into ChromaDB.
    files: [{"name": str, "bytes": bytes}, ...]
    """
    collection = reset_collection() if reset else get_collection()

    total_chunks = 0
    file_results = []

    for f in files:
        try:
            raw_text = extract_text(f["name"], f["bytes"])
            if not raw_text.strip():
                file_results.append({"file": f["name"], "status": "empty", "chunks": 0})
                continue

            chunks = chunk_text(raw_text, f["name"])
            if not chunks:
                file_results.append({"file": f["name"], "status": "no_chunks", "chunks": 0})
                continue

            texts     = [c["text"]   for c in chunks]
            ids       = [c["id"]     for c in chunks]
            metadatas = [{"source": c["source"], "chunk": c["chunk"]} for c in chunks]

            embeddings = embed_texts(texts)

            # Add in batches of 500
            batch = 500
            for i in range(0, len(chunks), batch):
                collection.add(
                    ids=ids[i:i+batch],
                    embeddings=embeddings[i:i+batch],
                    documents=texts[i:i+batch],
                    metadatas=metadatas[i:i+batch]
                )

            total_chunks += len(chunks)
            file_results.append({"file": f["name"], "status": "ok", "chunks": len(chunks)})

        except Exception as e:
            file_results.append({"file": f["name"], "status": f"error: {e}", "chunks": 0})

    return {"total_chunks": total_chunks, "files": file_results}

# ── Retrieval ─────────────────────────────────────────────────────────────────
def retrieve(query: str, top_k: int = 6) -> List[Dict[str, Any]]:
    """Retrieve top-k relevant chunks for a query."""
    collection = get_collection()
    count = collection.count()
    if count == 0:
        return []

    query_emb = genai.embed_content(
        model="models/text-embedding-004",
        content=query,
        task_type="retrieval_query"
    )["embedding"]

    results = collection.query(
        query_embeddings=[query_emb],
        n_results=min(top_k, count),
        include=["documents", "metadatas", "distances"]
    )

    retrieved = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        retrieved.append({
            "text":       doc,
            "source":     meta.get("source", "unknown"),
            "chunk":      meta.get("chunk", 0),
            "similarity": round(1 - dist, 3)
        })
    return retrieved

# ── Generation ────────────────────────────────────────────────────────────────
def answer_query(query: str, chat_history: List[Dict] = None) -> Dict[str, Any]:
    """Full RAG pipeline: retrieve → build prompt → generate with Gemini."""
    chunks = retrieve(query, top_k=6)

    if not chunks:
        return {
            "answer":   "No codebase indexed yet. Please upload your files first.",
            "sources":  [],
            "chunks":   []
        }

    # Build context
    context_parts = []
    sources_seen  = set()
    for c in chunks:
        context_parts.append(
            f"[Source: {c['source']} | Chunk {c['chunk']} | Similarity: {c['similarity']}]\n{c['text']}"
        )
        sources_seen.add(c["source"])

    context = "\n\n---\n\n".join(context_parts)

    system_prompt = """You are CodeMind, an expert enterprise AI assistant specialized in understanding internal codebases, technical documentation, and legacy systems.

Your role:
- Answer developer questions using ONLY the provided codebase context
- Explain code logic clearly with examples where helpful
- Identify patterns, anti-patterns, and potential issues
- Break down complex enterprise code into simple explanations
- Always cite which file/source your answer comes from

Rules:
- If the answer is not in the context, say "This information is not found in the indexed codebase."
- Always be precise and developer-friendly
- Format code snippets with proper markdown code blocks
- Mention the source file for every key point"""

    # Build conversation history
    history_text = ""
    if chat_history:
        for h in chat_history[-4:]:  # last 4 turns
            history_text += f"\nUser: {h['query']}\nCodeMind: {h['answer']}\n"

    user_prompt = f"""Codebase Context:
{context}

{f'Previous conversation:{history_text}' if history_text else ''}

Developer Question: {query}

Provide a clear, detailed answer based on the codebase context above."""

    model    = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        [{"role": "user", "parts": [system_prompt + "\n\n" + user_prompt]}],
        generation_config=genai.GenerationConfig(
            temperature=0.2,
            max_output_tokens=2048,
        )
    )

    return {
        "answer":  response.text,
        "sources": sorted(sources_seen),
        "chunks":  chunks
    }

def get_index_stats() -> Dict[str, Any]:
    """Return stats about the current index."""
    try:
        collection = get_collection()
        count = collection.count()
        if count == 0:
            return {"total_chunks": 0, "sources": []}
        # Get unique sources
        results = collection.get(include=["metadatas"])
        sources = list(set(m.get("source", "") for m in results["metadatas"]))
        return {"total_chunks": count, "sources": sorted(sources)}
    except Exception:
        return {"total_chunks": 0, "sources": []}
