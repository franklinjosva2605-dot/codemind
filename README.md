# 🧠 CodeMind — Enterprise Codebase Intelligence Assistant

> AI-powered assistant that transforms how enterprises interact with their internal codebases.
> Provides instant, context-aware answers to developer queries by indexing documentation and legacy code.

Built for **Lablab.ai — Transforming Enterprises Using AI Hackathon 2026**

---

## 🚀 Quick Start (5 Minutes)

### Step 1 — Clone & Setup
```bash
git clone https://github.com/yourusername/codemind
cd codemind
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2 — Set Your Gemini API Key
```bash
# Option A: Environment variable
export GEMINI_API_KEY="your_gemini_api_key_here"

# Option B: Enter directly in the Streamlit sidebar
```

### Step 3 — Run the App
```bash
# Streamlit UI (recommended)
streamlit run frontend/app.py

# OR FastAPI backend only
uvicorn backend.api:app --reload --port 8000
```

### Step 4 — Use It
1. Open browser at `http://localhost:8501`
2. Paste your Gemini API key in the sidebar
3. Upload your codebase files (multiple at once!)
4. Click **⚡ Index Files**
5. Ask anything about your code!

---

## 📁 Project Structure

```
codemind/
├── backend/
│   ├── engine.py          # Core RAG pipeline (indexing + retrieval + generation)
│   └── api.py             # FastAPI REST API
├── frontend/
│   └── app.py             # Streamlit UI
├── requirements.txt
└── README.md
```

---

## 🛠️ Tech Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| LLM         | Gemini 1.5 Flash (Google)           |
| Embeddings  | Gemini text-embedding-004           |
| Vector DB   | ChromaDB (local persistent)         |
| Backend     | FastAPI + Python                    |
| Frontend    | Streamlit                           |
| File Types  | .py .js .ts .go .java .md .pdf .txt .yaml .json + more |

---

## 🔌 REST API Usage

```bash
# Check health
curl http://localhost:8000/health

# Index files
curl -X POST http://localhost:8000/index \
  -F "files=@your_code.py" \
  -F "files=@README.md" \
  -F "reset=false"

# Query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How does authentication work?"}'

# Get stats
curl http://localhost:8000/stats
```

---

## ✨ Features

- **Multi-file upload** — Upload entire codebases at once
- **Multiple file types** — Python, JS, Go, Java, PDF, Markdown, YAML, JSON and more
- **Context-aware answers** — Gemini understands code structure and relationships
- **Source citations** — Every answer cites which file it came from
- **Conversation memory** — Maintains context across multiple questions
- **Similarity scoring** — Shows how relevant each retrieved chunk is
- **Persistent index** — ChromaDB saves your index between sessions
- **REST API** — Programmatic access for enterprise integration

---

## 💡 Example Questions to Ask

- *"What does this codebase do?"*
- *"Explain the authentication and authorization flow"*
- *"Where are database connections handled?"*
- *"What APIs are exposed and what do they do?"*
- *"Find any hardcoded credentials or security issues"*
- *"How is error handling implemented across the codebase?"*
- *"What design patterns are used?"*
- *"Explain the payment processing module"*

---

## 🏗️ How It Works

```
Upload Files → Extract Text → Chunk → Embed (Gemini) → Store (ChromaDB)
                                                              ↓
User Query → Embed Query → Retrieve Top-K Chunks → Build Prompt → Gemini LLM → Answer
```

1. **Ingestion** — Files are read, text extracted, split into overlapping chunks
2. **Embedding** — Each chunk is embedded using Gemini `text-embedding-004`
3. **Storage** — Embeddings stored in ChromaDB with metadata (source file, chunk index)
4. **Retrieval** — User query is embedded, top-6 similar chunks retrieved via cosine similarity
5. **Generation** — Gemini 1.5 Flash generates a contextual answer using retrieved chunks

---

## 👨‍💻 Author

**Franklin Josva A**
- Fiverr: fiverr.com/franklinjosva
- Built for Lablab.ai Enterprise AI Hackathon 2026
