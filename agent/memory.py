"""
agent/memory.py — Conversation Memory

WHAT IT DOES:
  Keeps a record of the full conversation (user + bot messages) so
  the chatbot can handle follow-up questions that refer to earlier turns.

WITHOUT MEMORY (stateless):
  User: "What companies did I work at?"
  Bot:  "TCS and Infosys"
  User: "What was my role at the second one?"
  Bot:  ← Has no idea what "second one" means — fails.

WITH MEMORY (stateful):
  Same conversation, but the bot sees the full history and correctly
  answers: "At Infosys you were a Senior Software Engineer."

WHY ConversationBufferMemory:
  - Stores the full conversation as plain text in RAM
  - Simple, zero dependencies, zero latency
  - Perfect for a single-session resume chatbot

FUTURE UPGRADE (for long chats or multi-session):
  - ConversationSummaryMemory: Summarizes old turns to save tokens
  - SQLiteChatMessageHistory: Persists history across app restarts
"""

class ChatMemory:
    """
    Pure-Python conversation memory (no LangChain dependency).
    Maintains a plain message list for the Streamlit UI and a
    formatted string for LLM context injection.

    NOTE: langchain.memory.ConversationBufferMemory was removed in
    LangChain 1.x. This implementation replaces it with a simple
    in-memory list that provides identical behaviour for this chatbot.
    """

    def __init__(self):
        # Simple list for the UI to iterate over and for LLM context
        self.messages: list[dict] = []

    def save(self, user_msg: str, ai_msg: str):
        """Record one conversation turn (user + bot)."""
        self.messages.append({"role": "user",      "content": user_msg})
        self.messages.append({"role": "assistant", "content": ai_msg})

    def get_history_string(self) -> str:
        """Return full conversation as a formatted string for LLM context."""
        lines = []
        for msg in self.messages:
            prefix = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"{prefix}: {msg['content']}")
        return "\n".join(lines)

    def clear(self):
        """Reset the conversation."""
        self.messages.clear()

    @property
    def is_empty(self) -> bool:
        return len(self.messages) == 0
