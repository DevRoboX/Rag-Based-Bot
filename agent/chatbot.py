"""
agent/chatbot.py — Main Chatbot Agent

WHAT IT DOES:
  The central controller. Receives user input, identifies intent,
  routes to the correct action (Q&A or Excel fill), and returns a response.

THIS IS THE BRAIN of the system:
  User message
    → Intent detection (intent.py)
    → Route to:
        QA          → RAG query → LLM answer
        FILL_ALL    → Read Excel fields → RAG per field → Write Excel
        FILL_SECTION→ Same as FILL_ALL but for one section only
        INGEST      → Re-run ingestion pipeline
        HELP        → Static help text

ALL RESPONSES go back through memory so the bot stays context-aware.
"""

import os
from rag.pipeline import RAGPipeline
from agent.intent import detect_intent, Intent
from agent.memory import ChatMemory
from excel.reader import get_all_fields, get_section_fields
from excel.mapper import fields_to_answers
from excel.writer import fill_excel
from config import EXCEL_TEMPLATE_PATH, EXCEL_OUTPUT_PATH, QA_LOG_PATH
from excel.qa_logger import export_session_to_excel

HELP_TEXT = """
**Resume RAG Bot - What I can do:**

**Ask me anything about your resume:**
   - "What are my technical skills?"
   - "List all companies I've worked at"
   - "What is my highest qualification?"
   - "Tell me about my projects"

**Fill the Excel sheet:**
   - "Fill the entire Excel sheet"
   - "Fill my skills section in Excel"
   - "Populate the education section"

**Export your Q&A session to Excel:**
   - "Export to Excel"
   - "Save my Q&A"
   - "Export chat"

**Reload resume data:**
   - "Reload my resume" (re-runs ingestion)

**Get help:**
   - "Help" / "What can you do?"
""".strip()


class ResumeBot:
    """
    Main chatbot agent — routes intents and coordinates all modules.
    Instantiate once; call .chat(user_input) for every message.
    """

    def __init__(self, rag_pipeline: RAGPipeline, memory: ChatMemory):
        self.rag = rag_pipeline
        self.memory = memory

    def chat(self, user_input: str) -> str:
        """
        Process one user message and return the bot's response.

        Args:
            user_input: Raw text from the user

        Returns:
            Bot response string (may include markdown formatting)
        """
        user_input = user_input.strip()
        if not user_input:
            return "Please type a message."

        intent = detect_intent(user_input)
        response = self._route(intent)

        # Save this exchange to memory for follow-up context
        self.memory.save(user_input, response)
        return response

    # ─── Intent Routing ───────────────────────────────────────────────────────

    def _route(self, intent: Intent) -> str:
        if intent.type == "HELP":
            return HELP_TEXT

        if intent.type == "INGEST":
            return self._handle_ingest()

        if intent.type == "QA":
            return self._handle_qa(intent.raw_query)

        if intent.type == "EXPORT_QA":
            return self._handle_export_qa()

        if intent.type == "FILL_ALL":
            return self._handle_fill_excel(section=None)

        if intent.type == "FILL_SECTION":
            return self._handle_fill_excel(section=intent.section)

        return "I didn't understand that. Type 'help' to see what I can do."

    # ─── Action Handlers ─────────────────────────────────────────────────────

    def _handle_qa(self, question: str) -> str:
        """Direct Q&A — retrieve from RAG and return answer."""
        result = self.rag.query(question)
        return result["answer"]

    def _handle_export_qa(self) -> str:
        """
        Export all Q&A pairs from the current session to Excel.
        Reads user+assistant pairs from memory and writes a formatted file.
        """
        # Extract Q&A pairs from memory (user msg + next assistant msg)
        qa_pairs = []
        messages = self.memory.messages
        for i in range(0, len(messages) - 1, 2):
            user_msg = messages[i]
            bot_msg  = messages[i + 1]
            # Only include actual Q&A turns (not export/fill commands)
            if user_msg["role"] == "user" and bot_msg["role"] == "assistant":
                question = user_msg["content"]
                answer   = bot_msg["content"]
                # Skip non-QA intents (help, fill, export commands themselves)
                from agent.intent import detect_intent
                if detect_intent(question).type == "QA":
                    qa_pairs.append((question, answer))

        if not qa_pairs:
            return (
                "No Q&A questions found in this session yet.\n"
                "Ask me some questions about your resume first, then say 'export to excel'!"
            )

        try:
            import os
            os.makedirs(os.path.dirname(QA_LOG_PATH) or ".", exist_ok=True)
            count = export_session_to_excel(qa_pairs, QA_LOG_PATH)
            return (
                f"**Exported {count} Q&A pairs to Excel!**\n\n"
                f"- File saved to: `{QA_LOG_PATH}`\n"
                f"- Download it from the **sidebar** on the left."
            )
        except Exception as e:
            return f"Export failed: {e}"

    def _handle_fill_excel(self, section: str | None) -> str:
        """
        Fill the Excel sheet (all fields or one section).

        Steps:
          1. Read field names from Excel template (Col A)
          2. For each field, run a RAG query to get the answer
          3. Write all answers into Col B of the output Excel
        """
        # Step 1: Get relevant fields from the Excel template
        if section:
            fields = get_section_fields(EXCEL_TEMPLATE_PATH, section)
            section_label = section.capitalize()
        else:
            fields = get_all_fields(EXCEL_TEMPLATE_PATH)
            section_label = "All"

        if not fields:
            return (
                f"⚠️ No fields found for section '{section}' in the template.\n"
                "Check that your Excel template has that section."
            )

        # Step 2: RAG query for every field
        print(f"[*] Querying RAG for {len(fields)} fields ...")
        answers = fields_to_answers(fields, self.rag)

        filled = sum(1 for v in answers.values() if v)
        skipped = len(answers) - filled

        # Step 3: Write to Excel
        os.makedirs(os.path.dirname(EXCEL_OUTPUT_PATH), exist_ok=True)
        fill_excel(answers, EXCEL_TEMPLATE_PATH, EXCEL_OUTPUT_PATH)

        return (
            f"✅ **Excel filled! ({section_label} section)**\n\n"
            f"- Fields found: **{filled}** / {len(fields)}\n"
            f"- Fields not found in resume: **{skipped}**\n\n"
            f"📁 Saved to: `{EXCEL_OUTPUT_PATH}`"
        )

    def _handle_ingest(self) -> str:
        """Trigger re-ingestion of the resume."""
        return (
            "🔄 To reload your resume, restart the app and run:\n"
            "```\npython setup.py\n```\n"
            "This will re-parse, re-chunk, and re-embed your resume."
        )
