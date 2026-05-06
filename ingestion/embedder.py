"""
ingestion/embedder.py — Vector Embedding and Storage

WHAT IT DOES:
  Converts text chunks → numerical vectors (embeddings)
  and persists them in ChromaDB for fast semantic search.

WHY BAAI/bge-base-en-v1.5:
  - FREE — runs locally via HuggingFace, no API costs
  - TOP-RANKED on MTEB benchmark (retrieval category)
  - LIGHTWEIGHT — 109M params, fast on CPU, ~440MB download (once)
  - normalize_embeddings=True enables accurate cosine similarity

WHY ChromaDB:
  - 100% local, no cloud, no Docker, no server setup
  - Persistent — embed once, load instantly on every future run
  - HNSW index → millisecond similarity search
"""

import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from config import EMBEDDING_MODEL, CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME


def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Load the BGE embedding model.
    Downloads ~440MB on first run, then uses local cache forever.
    """
    print(f"[*] Loading embedding model: {EMBEDDING_MODEL}")
    print("   (First run downloads ~440MB — cached for all future runs)")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},   # Change to "cuda" if you have a GPU
        encode_kwargs={"normalize_embeddings": True},
    )
    print("[OK] Embedding model ready")
    return embeddings


def build_vector_store(chunks: list) -> Chroma:
    """
    Embed all chunks and persist them in ChromaDB.

    This is a ONE-TIME operation. After this, load_vector_store() is used.

    Args:
        chunks: Chunked Document objects from chunker.py

    Returns:
        ChromaDB vector store instance
    """
    embeddings = get_embedding_model()

    print(f"[*] Embedding {len(chunks)} chunks -> storing in ChromaDB ...")
    print(f"   Save location: {CHROMA_PERSIST_DIR}")

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
        collection_name=CHROMA_COLLECTION_NAME,
    )

    print(f"[OK] Vector store built with {len(chunks)} vectors")
    print(f"   Persisted to: {CHROMA_PERSIST_DIR}")
    return vector_store


def load_vector_store() -> Chroma:
    """
    Load an existing ChromaDB from disk (after first ingestion).

    Raises FileNotFoundError if ingestion has not been run yet.
    """
    if not os.path.exists(CHROMA_PERSIST_DIR):
        raise FileNotFoundError(
            f"No vector store found at '{CHROMA_PERSIST_DIR}'.\n"
            "Run ingestion first:  python setup.py"
        )

    embeddings = get_embedding_model()

    vector_store = Chroma(
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=embeddings,
        collection_name=CHROMA_COLLECTION_NAME,
    )

    count = vector_store._collection.count()
    print(f"[OK] Loaded existing vector store ({count} vectors)")
    return vector_store
