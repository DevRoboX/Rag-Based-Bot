"""
rag/pipeline.py — End-to-End RAG Pipeline

WHAT IT DOES:
  Combines the retriever + generator into a single clean RAGPipeline
  class that the agent calls for every query.

THE RAG FLOW (every query):
  User question
    → embed question (same BGE model used during ingestion)
    → cosine search ChromaDB → Top-5 most relevant resume chunks
    → build prompt: [chunks as context] + [question]
    → send to Groq (LLaMA 3)
    → return clean answer

WHY A CLASS (not a function):
  - Holds the vector_store and llm as instance state
  - Avoids re-loading the LLM on every call
  - Clean interface: pipeline.query(question) is all the agent needs
"""

from langchain_community.vectorstores import Chroma
from rag.retriever import retrieve_chunks
from rag.generator import generate_answer, generate_excel_field_answer, get_llm
from config import TOP_K_RETRIEVAL


class RAGPipeline:
    """
    Main RAG pipeline — orchestrates retrieval and generation.
    Instantiate once and reuse for all queries.
    """

    def __init__(self, vector_store: Chroma):
        self.vector_store = vector_store
        self.llm = get_llm()
        print("[OK] RAG Pipeline ready")

    def query(self, question: str, top_k: int = TOP_K_RETRIEVAL) -> dict:
        """
        Full RAG query: retrieve + generate.

        Returns:
            {
              "answer"  : str   — LLM's answer
              "sources" : list  — retrieved Document chunks used
            }
        """
        chunks = retrieve_chunks(self.vector_store, question, top_k=top_k)

        if not chunks:
            return {
                "answer": "No relevant information found in the resume.",
                "sources": [],
            }

        answer = generate_answer(self.llm, question, chunks)
        return {"answer": answer, "sources": chunks}

    def query_for_excel_field(
        self,
        field_name: str,
        question: str,
        top_k: int = TOP_K_RETRIEVAL,
    ) -> str | None:
        """
        Retrieve + generate a concise value for a single Excel cell.

        Args:
            field_name : Excel column A label (e.g. "Email Address")
            question   : Query to locate the field value in the resume

        Returns:
            Short string for the cell, or None if not found
        """
        chunks = retrieve_chunks(self.vector_store, question, top_k=top_k)

        if not chunks:
            return None

        return generate_excel_field_answer(self.llm, field_name, question, chunks)
