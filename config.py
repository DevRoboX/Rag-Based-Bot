"""
config.py — Central Configuration

All settings live here. Change the MODEL names, paths, and parameters from
this single file without touching any other code.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# GROQ / LLM SETTINGS
# ─────────────────────────────────────────────
# You must set GROQ_API_KEY in a .env file
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Model to use from Groqs
GROQ_MODEL = "llama-3.3-70b-versatile"

# ─────────────────────────────────────────────
# EMBEDDING MODEL SETTINGS
# ─────────────────────────────────────────────
# HuggingFace model — downloaded once (~440MB), then cached locally
# Best free model for retrieval on MTEB benchmark
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"

# ─────────────────────────────────────────────
# CHROMADB / VECTOR STORE SETTINGS
# ─────────────────────────────────────────────
CHROMA_PERSIST_DIR = "./chroma_db"
CHROMA_COLLECTION_NAME = "resume_data"

# ─────────────────────────────────────────────
# FILE PATHS
# ─────────────────────────────────────────────
DATA_DIR = "./data"
EXCEL_TEMPLATE_PATH = "./data/excel_template.xlsx"
EXCEL_OUTPUT_PATH = "./output/filled_resume.xlsx"
# Auto-generated Q&A log — one row appended per chat question
QA_LOG_PATH = "./output/qa_log.xlsx"

# ─────────────────────────────────────────────
# RAG SETTINGS
# ─────────────────────────────────────────────
# Chunk size: ~500 chars ≈ 3-4 sentences — good for resume sections
CHUNK_SIZE = 500
# Overlap: 100 chars prevents losing context at chunk boundaries
CHUNK_OVERLAP = 100
# Top-K: retrieve the 5 most relevant chunks per query
TOP_K_RETRIEVAL = 5
