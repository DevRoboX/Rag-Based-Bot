"""
rag/generator.py — LLM Answer Generation

WHAT IT DOES:
  Takes retrieved resume chunks + a question, formats them into a
  prompt, sends to Groq (LLaMA 3), and returns a clean answer.

WHY THIS DESIGN:
  - We use TWO separate prompts:
    1. RAG_PROMPT        → for conversational Q&A (detailed answer)
    2. EXCEL_FIELD_PROMPT → for Excel filling (short, cell-appropriate)

  - Both prompts explicitly say "Use ONLY the context below."
    This GROUNDS the LLM — it cannot hallucinate or invent data.
    Everything it says must come from your actual resume text.

WHY TEMPERATURE = 0:
  For factual retrieval, we want deterministic answers.
  Temperature=0 → LLM always picks the highest-probability token.
  No creativity, no variation — just accurate extraction.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
from config import GROQ_MODEL

# Force reload .env every time this module is imported so new API keys
# are picked up immediately without restarting the process
load_dotenv(override=True)


# ─── Conversational Q&A Prompt ──────────────────────────────────────────────
RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are a helpful assistant that answers questions about a person's resume.
Use ONLY the information provided in the context below. Do not make up any information.
If the answer is not in the context, say "I couldn't find that in the resume."

Context (resume information):
{context}

Question: {question}

Instructions:
- Be concise and direct
- Extract exact facts from the context
- For lists (skills, companies), format them clearly
- Do not add any information not present in the context

Answer:""",
)

# ─── Excel Field Filling Prompt ──────────────────────────────────────────────
EXCEL_FIELD_PROMPT = PromptTemplate(
    input_variables=["context", "field_name", "question"],
    template="""You are extracting specific information from a resume to fill a single Excel cell.
Use ONLY the information provided in the context below.

Context (resume information):
{context}

Excel Field: {field_name}
Question: {question}

Instructions:
- Give a SHORT, DIRECT answer — this goes in a single Excel cell
- For lists, separate items with commas
- If not found, respond with exactly: NOT FOUND
- Do NOT include labels, explanations, or full sentences
- Maximum 200 characters

Answer:""",
)


def get_llm() -> BaseChatModel:
    """
    Initialize the Groq LLM (LLaMA 3).

    Prerequisites:
      1. GROQ_API_KEY set in .env
    """
    return ChatGroq(
        model_name=GROQ_MODEL,
        temperature=0,    # Deterministic — best for factual retrieval
    )


def generate_answer(llm: BaseChatModel, question: str, context_docs: list) -> str:
    """
    Generate a conversational answer from retrieved resume chunks.

    Args:
        llm          : Groq LLM instance
        question     : User's question
        context_docs : Retrieved Document chunks from ChromaDB

    Returns:
        Generated answer string
    """
    # Merge all retrieved chunks into one context block
    context = "\n\n---\n\n".join(doc.page_content for doc in context_docs)
    prompt = RAG_PROMPT.format(context=context, question=question)
    response = llm.invoke(prompt)
    return response.content.strip() if hasattr(response, 'content') else str(response).strip()


def generate_excel_field_answer(
    llm: BaseChatModel,
    field_name: str,
    question: str,
    context_docs: list,
) -> str | None:
    """
    Generate a short, Excel-cell-appropriate answer for a specific field.

    Args:
        llm          : Groq LLM instance
        field_name   : The Excel field label (e.g., "Technical Skills")
        question     : Query to find the field value
        context_docs : Retrieved Document chunks from ChromaDB

    Returns:
        Short answer string, or None if not found
    """
    context = "\n\n---\n\n".join(doc.page_content for doc in context_docs)
    prompt = EXCEL_FIELD_PROMPT.format(
        context=context,
        field_name=field_name,
        question=question,
    )
    response = llm.invoke(prompt)
    answer = response.content.strip() if hasattr(response, 'content') else str(response).strip()

    if "NOT FOUND" in answer.upper() or not answer:
        return None
    return answer
