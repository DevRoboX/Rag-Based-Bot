"""
agent/intent.py — Intent Detection

WHAT IT DOES:
  Reads the user's message and classifies it into one of 5 intents
  so the chatbot knows what action to take.

INTENT TYPES:
  FILL_ALL     → "Fill the entire Excel sheet"
  FILL_SECTION → "Fill only the skills section"
  EXPORT_QA    → "Export to Excel" / "Save my Q&A" / "Download chat"
  QA           → "What is my email?" / "List my projects"
  INGEST       → "Reload my resume" / "Re-index the data"
  HELP         → "What can you do?" / "Help"

WHY RULE-BASED (not an ML classifier):
  - A resume bot has a small, predictable set of intents
  - Keyword matching is instant, 100% local, zero latency
  - No extra model needed — simpler = more reliable
  - Easy to extend: just add keywords to the lists below
"""

from dataclasses import dataclass, field


@dataclass
class Intent:
    type: str                    # One of: FILL_ALL, FILL_SECTION, EXPORT_QA, QA, INGEST, HELP
    section: str | None = None   # Only set for FILL_SECTION
    raw_query: str = ""


# ─── Keyword Lists ────────────────────────────────────────────────────────────

FILL_ALL_KEYWORDS = [
    "fill", "populate", "complete", "fill out", "fill in",
    "update excel", "fill excel", "fill sheet", "fill all",
    "fill the excel", "fill everything", "complete the form",
    "fill form", "update sheet", "auto fill", "autofill",
    "write to excel", "add to excel",
]

# Maps each section → keywords that identify it
SECTION_KEYWORDS = {
    "skills":           ["skill", "technical", "technologies", "stack", "programming", "tools"],
    "experience":       ["experience", "work", "job", "employment", "career", "company", "employer"],
    "education":        ["education", "degree", "university", "college", "school", "qualification", "study"],
    "contact":          ["contact", "email", "phone", "address", "location", "linkedin", "mobile"],
    "summary":          ["summary", "objective", "profile", "about", "overview", "introduction"],
    "projects":         ["project", "projects", "portfolio", "built", "developed", "created"],
    "certifications":   ["certification", "certificate", "certified", "course", "credential"],
    "achievements":     ["achievement", "award", "honor", "recognition", "accomplishment", "prize"],
}

INGEST_KEYWORDS = [
    "ingest", "reload", "re-index", "reprocess", "load resume",
    "update resume", "refresh", "re-embed",
]

# Triggered when user says "export to excel", "save qa", "download chat" etc.
EXPORT_QA_KEYWORDS = [
    "export to excel", "export chat", "export qa", "export questions",
    "save qa", "save chat", "save to excel", "download qa",
    "download chat", "export conversation", "save conversation",
    "export my questions", "export answers",
]

HELP_KEYWORDS = [
    "help", "what can you do", "commands", "how to use",
    "instructions", "guide", "options",
]


# ─── Main Classifier ──────────────────────────────────────────────────────────

def detect_intent(user_input: str) -> Intent:
    """
    Classify user input into an Intent.

    Logic order:
      1. Check HELP        → user wants usage info
      2. Check INGEST      → user wants to reload resume data
      3. Check EXPORT_QA   → user wants to export Q&A session to Excel
      4. Check FILL        → user wants Excel filled
         4a. Check if a specific section is mentioned → FILL_SECTION
         4b. Otherwise                                → FILL_ALL
      5. Default → QA (direct question about the resume)
    """
    lower = user_input.lower().strip()

    if any(kw in lower for kw in HELP_KEYWORDS):
        return Intent(type="HELP", raw_query=user_input)

    if any(kw in lower for kw in INGEST_KEYWORDS):
        return Intent(type="INGEST", raw_query=user_input)

    # Check EXPORT_QA before FILL_ALL to avoid conflict
    if any(kw in lower for kw in EXPORT_QA_KEYWORDS):
        return Intent(type="EXPORT_QA", raw_query=user_input)

    if any(kw in lower for kw in FILL_ALL_KEYWORDS):
        # Check if a specific section is also mentioned
        for section, keywords in SECTION_KEYWORDS.items():
            if any(kw in lower for kw in keywords):
                return Intent(type="FILL_SECTION", section=section, raw_query=user_input)
        return Intent(type="FILL_ALL", raw_query=user_input)

    # Default — treat as a direct resume question
    return Intent(type="QA", raw_query=user_input)
