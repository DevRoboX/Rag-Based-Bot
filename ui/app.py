"""
ui/app.py — Streamlit Chat Interface

WHAT IT DOES:
  Provides a beautiful, interactive chat UI where you can:
  - Ask questions about your resume
  - Command the bot to fill the Excel sheet
  - Download the filled Excel file directly from the browser

WHY STREAMLIT:
  - Pure Python — no HTML/CSS/JS needed
  - Built-in chat_message and chat_input components
  - session_state handles the bot/memory lifecycle across rerenders
  - Ships a local web server instantly with: streamlit run ui/app.py

HOW SESSION STATE WORKS:
  Streamlit re-runs the entire script on every user interaction.
  st.session_state persists objects (like the RAGPipeline and ChatMemory)
  across reruns so we don't reload models on every message.
"""

import sys
import os

# ── Force UTF-8 stdout/stderr on Windows ──────────────────────────────────────
# Windows terminals default to cp1252, which crashes on emoji printed by
# HuggingFace, sentence-transformers, tqdm and other libraries.
# Reconfiguring stdout/stderr to UTF-8 fixes this permanently for all sources.
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
# ──────────────────────────────────────────────────────────────────────────────

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from ingestion.embedder import load_vector_store
from rag.pipeline import RAGPipeline
from agent.chatbot import ResumeBot
from agent.memory import ChatMemory
from config import EXCEL_OUTPUT_PATH, GROQ_MODEL, QA_LOG_PATH

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Resume RAG Bot",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main { background: #0f1117; }

    /* Chat bubble styles */
    [data-testid="stChatMessage"] {
        border-radius: 12px;
        margin-bottom: 8px;
        padding: 4px 8px;
    }

    /* Header gradient */
    .hero-header {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%);
        padding: 28px 32px;
        border-radius: 16px;
        margin-bottom: 24px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(99,102,241,0.3);
    }
    .hero-header h1 { color: white; font-size: 2rem; font-weight: 700; margin: 0; }
    .hero-header p  { color: rgba(255,255,255,0.85); margin: 6px 0 0 0; font-size: 1rem; }

    /* Sidebar */
    [data-testid="stSidebar"] { background: #1a1d2e; }

    /* Status badge */
    .status-ok   { color: #4ade80; font-weight: 600; }
    .status-err  { color: #f87171; font-weight: 600; }

    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 600;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ─── Hero Header ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
    <h1>🤖 Resume RAG Bot</h1>
    <p>Ask questions about your resume · Auto-fill Excel sheets with AI</p>
</div>
""", unsafe_allow_html=True)


# ─── Session State Initialization ────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading RAG pipeline (first time is slower)...")
def load_pipeline(groq_model: str):
    """
    Load once and cache across all reruns.
    groq_model is passed as a parameter so that changing the model in
    config.py automatically invalidates the cache — no restart needed.
    """
    vector_store = load_vector_store()
    rag = RAGPipeline(vector_store)
    return rag


# Initialize memory and bot (once per session)
if "memory" not in st.session_state:
    st.session_state.memory = ChatMemory()

if "bot" not in st.session_state:
    try:
        rag = load_pipeline(GROQ_MODEL)  # model name busts cache on change
        st.session_state.bot = ResumeBot(rag, st.session_state.memory)
        st.session_state.ready = True
    except FileNotFoundError:
        st.session_state.bot = None
        st.session_state.ready = False

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ System Status")

    if st.session_state.get("ready"):
        st.markdown('<p class="status-ok">✅ RAG Pipeline Ready</p>', unsafe_allow_html=True)
        st.markdown('<p class="status-ok">✅ LLM (LLaMA 3) Connected</p>', unsafe_allow_html=True)
        st.markdown('<p class="status-ok">✅ ChromaDB Loaded</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="status-err">❌ Vector store not found</p>', unsafe_allow_html=True)
        st.info("Run `python setup.py` first to ingest your resume.")

    st.markdown("---")
    st.markdown("### 💡 Try These Commands")
    example_commands = [
        "What are my technical skills?",
        "List all companies I worked at",
        "Fill the entire Excel sheet",
        "Fill my skills section in Excel",
        "What is my highest qualification?",
        "Tell me about my projects",
    ]
    for cmd in example_commands:
        if st.button(f"▶ {cmd}", key=cmd):
            st.session_state.pending_input = cmd

    st.markdown("---")

    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.memory.clear()
        st.rerun()

    # Download filled Excel (if it exists)
    if os.path.exists(EXCEL_OUTPUT_PATH):
        st.markdown("### Download Excel")
        with open(EXCEL_OUTPUT_PATH, "rb") as f:
            st.download_button(
                label="Download Filled Excel",
                data=f,
                file_name="filled_resume.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_filled",
            )

    # Download Q&A Report (if it exists) ── generated on "export to excel" command
    if os.path.exists(QA_LOG_PATH):
        st.markdown("### Client Q&A Report")
        st.caption("Generated when you say 'export to excel' in chat.")
        with open(QA_LOG_PATH, "rb") as f:
            st.download_button(
                label="Download Q&A Report (.xlsx)",
                data=f,
                file_name="qa_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_qa_log",
            )
    # ─────────────────────────────────────────────────────────────────────

    st.markdown("---")
    st.markdown("**Model:** LLaMA 3 (Groq)")
    st.markdown("**Embeddings:** BAAI/bge-base")
    st.markdown("**Vector DB:** ChromaDB")


# ─── Not Ready Warning ───────────────────────────────────────────────────────
if not st.session_state.get("ready"):
    st.error(
        "⚠️ **Resume not ingested yet!**\n\n"
        "Please run the setup script first:\n"
        "```\npython setup.py\n```\n"
        "Then restart this app."
    )
    st.stop()


# ─── Chat History Display ─────────────────────────────────────────────────────
for msg in st.session_state.memory.messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])


# ─── Chat Input ──────────────────────────────────────────────────────────────
# Handle sidebar button clicks
if "pending_input" in st.session_state:
    user_input = st.session_state.pop("pending_input")
else:
    user_input = st.chat_input("Ask about your resume or say 'Fill my Excel sheet'...")

if user_input:
    # Display user message
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # Generate and display bot response
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.bot.chat(user_input)
            except Exception as e:
                err = str(e)
                if "rate_limit_exceeded" in err or "429" in err:
                    import re
                    wait = re.search(r"try again in (\S+)", err)
                    wait_msg = f" Please wait **{wait.group(1)}** and try again." if wait else ""
                    response = (
                        "**Rate limit reached** - you've used up today's free token allowance on Groq.\n\n"
                        f"{wait_msg}\n\n"
                        "> **Tip:** The free tier resets every 24 hours. "
                        "You can also upgrade at [console.groq.com/settings/billing](https://console.groq.com/settings/billing)."
                    )
                    st.session_state.memory.save(user_input, response)
                else:
                    response = f"**Error:** {err}"
                    st.session_state.memory.save(user_input, response)
        st.markdown(response)

    # Refresh sidebar download button if Excel or Q&A log was just updated
    if os.path.exists(EXCEL_OUTPUT_PATH) or os.path.exists(QA_LOG_PATH):
        st.rerun()

