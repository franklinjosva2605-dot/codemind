"""
CodeMind — Enterprise Codebase Intelligence Assistant
Streamlit Frontend
"""

import os
import sys
import streamlit as st
#keep your path fix
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import backend functions (Make sure "from" starts on a new line)
from backend.engine import index_files, answer_query, get_index_stats

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CodeMind — Enterprise AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Base */
[data-testid="stAppViewContainer"] { background: #0d1117; }
[data-testid="stSidebar"] { background: #161b22; border-right: 1px solid #30363d; }
[data-testid="stHeader"] { background: transparent; }

/* Typography */
h1, h2, h3 { color: #e6edf3 !important; }
p, li, label { color: #8b949e !important; }
.stMarkdown p { color: #c9d1d9 !important; }

/* Logo area */
.logo-area {
    background: linear-gradient(135deg, #1f6feb 0%, #388bfd 100%);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    margin-bottom: 20px;
}
.logo-area h2 { color: white !important; margin: 0; font-size: 1.6rem; }
.logo-area p { color: rgba(255,255,255,0.8) !important; margin: 4px 0 0 0; font-size: 0.85rem; }

/* Stat cards */
.stat-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    margin-bottom: 10px;
}
.stat-num { font-size: 2rem; font-weight: bold; color: #1f6feb; }
.stat-label { font-size: 0.8rem; color: #8b949e; margin-top: 4px; }

/* Chat bubbles */
.user-bubble {
    background: #1f6feb;
    color: white;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 16px;
    margin: 8px 0;
    max-width: 80%;
    margin-left: auto;
    font-size: 0.95rem;
}
.ai-bubble {
    background: #161b22;
    border: 1px solid #30363d;
    color: #c9d1d9;
    border-radius: 18px 18px 18px 4px;
    padding: 14px 18px;
    margin: 8px 0;
    max-width: 90%;
    font-size: 0.92rem;
    line-height: 1.6;
}
.source-badge {
    display: inline-block;
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.75rem;
    color: #58a6ff;
    margin: 3px 3px 0 0;
}
.chat-container {
    height: 480px;
    overflow-y: auto;
    padding: 10px;
    border: 1px solid #30363d;
    border-radius: 12px;
    background: #0d1117;
    margin-bottom: 12px;
}
.welcome-msg {
    text-align: center;
    padding: 60px 20px;
    color: #8b949e;
}
.welcome-msg h3 { color: #58a6ff !important; }

/* Upload area */
.upload-section {
    background: #161b22;
    border: 2px dashed #30363d;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
}

/* Buttons */
.stButton button {
    background: #1f6feb !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 8px 20px !important;
    width: 100% !important;
}
.stButton button:hover {
    background: #388bfd !important;
}

/* File list */
.file-item {
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 4px 0;
    font-size: 0.82rem;
    color: #8b949e;
}
.file-ok { border-left: 3px solid #3fb950; }
.file-err { border-left: 3px solid #f85149; }

/* Similarity badge */
.sim-high { color: #3fb950; }
.sim-med  { color: #d29922; }
.sim-low  { color: #f85149; }

/* Suggestion chips */
.chip {
    display: inline-block;
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 0.8rem;
    color: #58a6ff;
    margin: 3px;
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
if "chat_history"  not in st.session_state: st.session_state.chat_history  = []
if "indexed"       not in st.session_state: st.session_state.indexed        = False
if "index_stats"   not in st.session_state: st.session_state.index_stats    = {"total_chunks": 0, "sources": []}
if "query_input"   not in st.session_state: st.session_state.query_input    = ""

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="logo-area">
        <h2>🧠 CodeMind</h2>
        <p>Enterprise Codebase Intelligence</p>
    </div>
    """, unsafe_allow_html=True)

    # API Key
    st.markdown("**🔑 Gemini API Key**")
    #api_key = st.text_input("", type="password",
    #placeholder="Paste your Gemini API key",
    #key="api_key_input",
        #label_visibility="collapsed")
api_key = st.secrets["GEMINI_API_KEY"]
if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
        import google.generativeai as genai
        genai.configure(api_key=api_key)

st.markdown("---")

    # Stats
stats = get_index_stats()
st.session_state.index_stats = stats

col1, col2 = st.columns(2)
with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-num">{stats['total_chunks']}</div>
            <div class="stat-label">Chunks Indexed</div>
        </div>""", unsafe_allow_html=True)
with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-num">{len(stats['sources'])}</div>
            <div class="stat-label">Files Indexed</div>
        </div>""", unsafe_allow_html=True)

st.markdown("---")

    # File Upload
st.markdown("**📁 Upload Codebase Files**")
st.caption("Supports: .py .js .ts .go .java .md .txt .pdf .yaml .json .html .css .env .sh")

uploaded_files = st.file_uploader(
        "Drop files here",
        accept_multiple_files=True,
        type=["py","js","ts","go","java","md","txt","pdf",
              "yaml","yml","json","html","css","sh","env",
              "jsx","tsx","cpp","c","rs","rb","php","cs"],
        label_visibility="collapsed"
    )

reset_index = st.checkbox("🔄 Reset existing index", value=False)

if st.button("⚡ Index Files", disabled=not uploaded_files):
        if not api_key:
            st.error("Please enter your Gemini API key first!")
        else:
            files_data = [{"name": f.name, "bytes": f.read()} for f in uploaded_files]
            with st.spinner(f"Indexing {len(files_data)} files..."):
                try:
                    result = index_files(files_data, reset=reset_index)
                    st.session_state.indexed = True
                    st.session_state.index_stats = get_index_stats()

                    # Show results
                    for fr in result["files"]:
                        status_class = "file-ok" if fr["status"] == "ok" else "file-err"
                        icon = "✅" if fr["status"] == "ok" else "❌"
                        st.markdown(f"""
                        <div class="file-item {status_class}">
                            {icon} <b>{fr['file']}</b> — {fr['chunks']} chunks
                        </div>""", unsafe_allow_html=True)

                    st.success(f"✅ Indexed {result['total_chunks']} total chunks!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

st.markdown("---")

    # Indexed files list
if stats["sources"]:
        st.markdown("**📂 Indexed Files**")
        for src in stats["sources"]:
            st.markdown(f"""
            <div class="file-item file-ok">
                📄 {src}
            </div>""", unsafe_allow_html=True)

st.markdown("---")
if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

st.markdown("---")
st.caption("Built for Lablab.ai Enterprise AI Hackathon 2026")
st.caption("Powered by Gemini 1.5 Flash + ChromaDB")

# ── Main Area ─────────────────────────────────────────────────────────────────
st.markdown("## 🧠 CodeMind — Enterprise Codebase Intelligence")
st.caption("Ask anything about your internal codebase. Instant, context-aware answers.")

# Suggested questions
if not st.session_state.chat_history:
    st.markdown("**💡 Try asking:**")
    suggestions = [
        "What does this codebase do?",
        "Explain the authentication flow",
        "Where are database connections handled?",
        "What APIs are exposed?",
        "Find any hardcoded secrets or issues",
        "How is error handling implemented?",
    ]
    cols = st.columns(3)
    for i, sug in enumerate(suggestions):
        with cols[i % 3]:
            if st.button(sug, key=f"sug_{i}"):
                st.session_state.query_input = sug
                st.rerun()

# Chat history display
chat_html = '<div class="chat-container">'

if not st.session_state.chat_history:
    chat_html += """
    <div class="welcome-msg">
        <h3>👋 Welcome to CodeMind</h3>
        <p>Upload your codebase files in the sidebar, then ask me anything about your code.</p>
        <p>I'll provide instant, context-aware answers from your indexed codebase.</p>
    </div>"""
else:
    for turn in st.session_state.chat_history:
        # User message
        chat_html += f'<div class="user-bubble">🧑‍💻 {turn["query"]}</div>'
        # AI answer
        answer_html = turn["answer"].replace("\n", "<br>")
        sources_html = " ".join(
            f'<span class="source-badge">📄 {s}</span>'
            for s in turn.get("sources", [])
        )
        chat_html += f"""
        <div class="ai-bubble">
            <b>🧠 CodeMind</b><br><br>
            {answer_html}
            {f'<br><br><b>Sources:</b> {sources_html}' if sources_html else ''}
        </div>"""

chat_html += "</div>"
st.markdown(chat_html, unsafe_allow_html=True)

# ── Query Input ───────────────────────────────────────────────────────────────
col_input, col_btn = st.columns([5, 1])

with col_input:
    query = st.text_input(
        "Ask about your codebase...",
        value=st.session_state.query_input,
        placeholder="e.g. How does the payment processing work?",
        key="query_field",
        label_visibility="collapsed"
    )

with col_btn:
    send = st.button("Send 🚀")

# Handle send
if (send or query) and query.strip():
    if not api_key:
        st.error("⚠️ Please enter your Gemini API key in the sidebar!")
    elif stats["total_chunks"] == 0:
        st.warning("⚠️ Please upload and index your codebase files first!")
    else:
        with st.spinner("🔍 Searching codebase & generating answer..."):
            try:
                result = answer_query(
                    query=query,
                    chat_history=st.session_state.chat_history
                )
                st.session_state.chat_history.append({
                    "query":   query,
                    "answer":  result["answer"],
                    "sources": result["sources"],
                    "chunks":  result["chunks"]
                })
                st.session_state.query_input = ""

                # Show retrieved chunks in expander
                if result["chunks"]:
                    with st.expander(f"🔍 Retrieved {len(result['chunks'])} context chunks"):
                        for i, chunk in enumerate(result["chunks"]):
                            sim = chunk["similarity"]
                            sim_class = "sim-high" if sim > 0.7 else ("sim-med" if sim > 0.5 else "sim-low")
                            st.markdown(f"""
                            **Chunk {i+1}** — 📄 `{chunk['source']}` |
                            Similarity: <span class="{sim_class}">{sim}</span>
                            """, unsafe_allow_html=True)
                            st.code(chunk["text"][:400] + ("..." if len(chunk["text"]) > 400 else ""),
                                   language="text")

                st.rerun()
            except Exception as e:
                st.error(f"Error generating answer: {e}")
# ── Bottom Info ────────────────────────────────────────────────────────────────
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📦 Chunks Indexed", stats["total_chunks"])
with col2:
    st.metric("📁 Files Indexed", len(stats["sources"]))
with col3:
    st.metric("💬 Questions Asked", len(st.session_state.chat_history))
