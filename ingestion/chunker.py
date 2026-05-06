"""
ingestion/chunker.py — Text Chunker / Splitter

WHAT IT DOES:
  Splits the loaded resume into smaller overlapping chunks
  that are optimal for embedding and retrieval.

WHY WE CHUNK:
  - LLMs and embedding models have token limits (~512 for BGE)
  - Smaller chunks → more precise retrieval (find exactly what's asked)
  - Overlap (100 chars) prevents losing context at chunk boundaries

CHUNK STRATEGY:
  Size 500 chars ≈ 3-4 sentences — large enough to hold a full
  job description, small enough to be specific.

  Separators tried in order:
    1. \\n\\n (paragraph break) — most natural split point
    2. \\n    (line break)
    3. .      (sentence end)
    4. space  (last resort word boundary)
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


def chunk_documents(
    documents: list,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> list:
    """
    Split documents into overlapping chunks.

    Args:
        documents    : LangChain Document objects from loader
        chunk_size   : Max characters per chunk
        chunk_overlap: Characters shared between adjacent chunks

    Returns:
        List of chunked Document objects
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    chunks = splitter.split_documents(documents)

    # Tag each chunk with its index for debugging / tracing
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
        chunk.metadata["chunk_total"] = len(chunks)

    print(
        f"✂️  Split into {len(chunks)} chunks "
        f"(size={chunk_size}, overlap={chunk_overlap})"
    )
    return chunks
