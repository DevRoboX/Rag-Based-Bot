"""
ingestion/loader.py — Resume Document Loader

WHAT IT DOES:
  Loads your resume file (PDF or DOCX) and converts it into
  LangChain Document objects — the standard unit of text in LangChain.

WHY:
  Different file formats need different parsers. We abstract this
  away so the rest of the code always receives the same Document format
  regardless of whether the source is PDF, DOCX, or plain text.
"""

from pathlib import Path
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader
from langchain_core.documents import Document


def load_resume(file_path: str) -> list:
    """
    Load a resume file → list of LangChain Document objects.

    Each Document has:
      - page_content : the raw text
      - metadata     : source filename, file type, page number
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    ext = path.suffix.lower()
    print(f"[*] Loading resume: {path.name}")

    if ext == ".pdf":
        # PyMuPDF is faster and more accurate than PyPDFLoader for text extraction
        loader = PyMuPDFLoader(str(path))
    elif ext in [".docx", ".doc"]:
        loader = Docx2txtLoader(str(path))
    elif ext == ".txt":
        from langchain_community.document_loaders import TextLoader
        loader = TextLoader(str(path), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported format: {ext}. Use .pdf, .docx, or .txt")

    documents = loader.load()

    # Enrich metadata so we can trace answers back to their source later
    for doc in documents:
        doc.metadata["source_file"] = path.name
        doc.metadata["file_type"] = ext

    print(f"[OK] Loaded {len(documents)} page(s)")
    return documents


def load_all_from_dir(directory: str) -> list:
    """Load ALL supported resume files from a directory."""
    supported = [".pdf", ".docx", ".doc", ".txt"]
    all_docs = []

    for f in Path(directory).iterdir():
        if f.suffix.lower() in supported:
            all_docs.extend(load_resume(str(f)))

    if not all_docs:
        raise ValueError(f"No supported files found in {directory}")

    return all_docs
