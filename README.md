# 🤖 RAG-Based Resume Chatbot → Excel Filler

A fully local, free AI chatbot that reads your resume, stores it in a
vector database, and auto-fills an Excel sheet — all using open-source
models running on your own machine.

---

## 🚀 Quick Start (5 Steps)

### Step 1 — Get a Groq API Key
1. Go to https://console.groq.com/keys and create a free account.
2. Generate an API Key.
3. Create a `.env` file in the project root and add your key:
```env
GROQ_API_KEY=your_api_key_here
```

### Step 2 — Install Python Dependencies
```bash
cd "c:\Users\HP\Desktop\Rag Based Bot"
pip install -r requirements.txt
```
> First run downloads the BGE embedding model (~440MB). This is a one-time download.

### Step 3 — Add Your Resume
Copy your resume file into the `data/` folder:
```
data/
  your_resume.pdf    ← place your file here (.pdf, .docx, or .txt)
```

### Step 4 — Run Setup (One Time Only)
```bash
python setup.py
```
This will:
- ✅ Create `data/excel_template.xlsx` with all resume fields
- ✅ Parse & chunk your resume
- ✅ Embed chunks using BAAI/bge-base-en-v1.5
- ✅ Store vectors in `./chroma_db/`

### Step 5 — Launch the Chatbot
```bash
streamlit run ui/app.py
```
Open your browser → `http://localhost:8501`

---

## 💬 What You Can Say

| Command | What Happens |
|---|---|
| `"Fill the entire Excel sheet"` | Fills ALL fields in the Excel sheet |
| `"Fill my skills section"` | Fills only Skills section fields |
| `"Fill education in Excel"` | Fills only Education section |
| `"What are my technical skills?"` | Direct Q&A answer |
| `"List all companies I worked at"` | Direct Q&A answer |
| `"What is my email address?"` | Direct Q&A answer |
| `"Help"` | Shows all commands |

---

## 📁 Project Structure

```
Rag Based Bot/
├── data/
│   ├── your_resume.pdf          ← PUT YOUR RESUME HERE
│   └── excel_template.xlsx      ← auto-created by setup.py
├── output/
│   └── filled_resume.xlsx       ← auto-created when you fill Excel
├── chroma_db/                   ← auto-created by setup.py
├── ingestion/
│   ├── loader.py                # Parse PDF/DOCX → Documents
│   ├── chunker.py               # Split into 500-char chunks
│   └── embedder.py              # Embed with BGE → ChromaDB
├── rag/
│   ├── retriever.py             # Semantic search ChromaDB
│   ├── generator.py             # LLM answer generation
│   └── pipeline.py              # End-to-end RAG orchestration
├── agent/
│   ├── intent.py                # Classify user message intent
│   ├── memory.py                # Conversation history
│   └── chatbot.py               # Main chatbot controller
├── excel/
│   ├── reader.py                # Read fields from Excel template
│   ├── mapper.py                # Map fields → RAG queries → answers
│   └── writer.py                # Write answers into Excel cells
├── ui/
│   └── app.py                   # Streamlit chat UI
├── config.py                    # All settings (models, paths, etc.)
├── setup.py                     # One-time setup entry point
└── requirements.txt
```

---

## ⚙️ Configuration

Edit `config.py` to change models or paths:

```python
GROQ_MODEL      = "llama3-8b-8192"

EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"  # free, top retrieval benchmark
CHUNK_SIZE      = 500                       # characters per chunk
CHUNK_OVERLAP   = 100                       # overlap between chunks
TOP_K_RETRIEVAL = 5                         # resume chunks retrieved per query
```

---

## 🔧 Troubleshooting

| Problem | Fix |
|---|---|
| `API Key Error` | Ensure you created a `.env` file with `GROQ_API_KEY` |
| `Rate Limit` | Groq has rate limits on the free tier, wait a minute |
| `No vector store found` | Run `python setup.py` |
| `No files in data/` | Copy your resume PDF to `./data/` |
| Slow first response | BGE model loading — normal, ~10s on first query |
| Wrong answers | Resume chunks may be too large — reduce `CHUNK_SIZE` in config.py |

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| LLM | Groq + LLaMA 3 8B (cloud, free, fast) |
| Embeddings | BAAI/bge-base-en-v1.5 (local, free) |
| Vector Store | ChromaDB (local, persistent) |
| Agent Framework | LangChain |
| Memory | ConversationBufferMemory |
| Excel I/O | openpyxl |
| UI | Streamlit |
