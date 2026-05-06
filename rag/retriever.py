"""
rag/retriever.py — Semantic Search Over ChromaDB

WHAT IT DOES:
  Takes a user query, embeds it using the same BGE model used during
  ingestion, then finds the most semantically similar resume chunks
  stored in ChromaDB.

HOW SEMANTIC SEARCH WORKS (step by step):
  1. User asks: "What programming languages do I know?"
  2. The query is embedded → a 768-dim vector
  3. ChromaDB computes cosine similarity of that vector against ALL
     stored chunk vectors
  4. Returns the Top-K chunks whose text is most similar in meaning
  5. Those chunks contain your actual resume text about languages

WHY cosine similarity:
  Measures the ANGLE between vectors, not their magnitude.
  Works perfectly for normalized embeddings (which BGE gives us).
  Score of 1.0 = identical meaning, 0.0 = unrelated.

WHY TOP_K = 5:
  k=1-2  → too narrow, may miss relevant context
  k=10+  → adds noise, LLM gets confused by irrelevant chunks
  k=5    → sweet spot for resume-length documents
"""

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from config import TOP_K_RETRIEVAL


def get_retriever(vector_store: Chroma, top_k: int = TOP_K_RETRIEVAL):
    """
    Return a LangChain Retriever object from the vector store.
    Used by LangChain chains that expect a retriever interface.
    """
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": top_k},
    )


def retrieve_chunks(
    vector_store: Chroma,
    query: str,
    top_k: int = TOP_K_RETRIEVAL,
) -> list:
    """
    Retrieve the top-K most relevant resume chunks for a query.

    Args:
        vector_store : ChromaDB instance
        query        : Natural language search query
        top_k        : Number of chunks to return

    Returns:
        List of Document objects (most relevant resume chunks)
    """
    results = vector_store.similarity_search(query, k=top_k)
    return results


def retrieve_with_scores(
    vector_store: Chroma,
    query: str,
    top_k: int = TOP_K_RETRIEVAL,
) -> list:
    """
    Retrieve chunks along with their similarity scores (for debugging).

    Returns:
        List of (Document, score) tuples — score closer to 1.0 = more relevant
    """
    return vector_store.similarity_search_with_score(query, k=top_k)
