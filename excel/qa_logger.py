"""
excel/qa_logger.py — Auto Q&A Excel Logger

WHAT IT DOES:
  Every time the user asks a question and gets an answer from the RAG bot,
  this module appends a new row to a running Excel log:

      | Question                          | Answer                        |
      |-----------------------------------|-------------------------------|
      | What are my technical skills?     | Python, React, SQL, Docker... |
      | What is my highest degree?        | B.Tech in Computer Science    |

  The file grows with every chat exchange — one row per Q&A pair.
  The user can download this log from the Streamlit sidebar at any time.

WHY A SEPARATE FILE (not the resume template):
  - Keeps the existing Excel fill feature untouched
  - This log is purely additive — a living record of every question asked
  - Makes it easy to export a session's Q&A for sharing or review
"""

import os
from datetime import datetime
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side


# ── Style constants ───────────────────────────────────────────────────────────
HEADER_FILL   = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
HEADER_FONT   = Font(bold=True, color="FFFFFF", size=11)
Q_FILL        = PatternFill(start_color="EEF2FF", end_color="EEF2FF", fill_type="solid")
A_FILL        = PatternFill(start_color="F0FDF4", end_color="F0FDF4", fill_type="solid")
Q_FONT        = Font(bold=True, color="3730A3", size=10)
A_FONT        = Font(bold=False, color="166534", size=10)
THIN_BORDER   = Border(
    bottom=Side(style="thin", color="E5E7EB"),
    left=Side(style="thin",   color="E5E7EB"),
    right=Side(style="thin",  color="E5E7EB"),
)
WRAP_ALIGN    = Alignment(vertical="center", wrap_text=True, horizontal="left")
CENTER_ALIGN  = Alignment(vertical="center", horizontal="center")


def _create_fresh_workbook(filepath: str) -> openpyxl.Workbook:
    """Create a brand-new Q&A log workbook with styled headers."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Q&A Log"

    # Column widths
    ws.column_dimensions["A"].width = 5   # Row #
    ws.column_dimensions["B"].width = 55  # Question
    ws.column_dimensions["C"].width = 75  # Answer
    ws.column_dimensions["D"].width = 22  # Timestamp

    # Header row
    headers = ["#", "Question", "Answer", "Timestamp"]
    for col, title in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=title)
        cell.fill      = HEADER_FILL
        cell.font      = HEADER_FONT
        cell.alignment = CENTER_ALIGN
    ws.row_dimensions[1].height = 26

    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    wb.save(filepath)
    return wb


def log_qa_to_excel(question: str, answer: str, filepath: str) -> None:
    """
    Append one Q&A pair as a new row in the log Excel file.

    Creates the file with headers if it doesn't exist yet.

    Args:
        question : The user's question string
        answer   : The bot's answer string
        filepath : Path to the Q&A log Excel file (from config.QA_LOG_PATH)
    """
    # Load existing workbook or create a new one
    if os.path.exists(filepath):
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
    else:
        _create_fresh_workbook(filepath)
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active

    # Next row index (skip header row 1)
    next_row = ws.max_row + 1
    row_num  = next_row - 1  # Row number shown to user (1-based, excluding header)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data = [row_num, question, answer, timestamp]
    fills = [None, Q_FILL, A_FILL, None]
    fonts = [None, Q_FONT, A_FONT, None]

    for col, (value, fill, font) in enumerate(zip(data, fills, fonts), start=1):
        cell = ws.cell(row=next_row, column=col, value=value)
        cell.border    = THIN_BORDER
        cell.alignment = WRAP_ALIGN if col in (2, 3) else CENTER_ALIGN
        if fill:
            cell.fill = fill
        if font:
            cell.font = font

    ws.row_dimensions[next_row].height = 60  # Tall enough for wrapped text

    wb.save(filepath)
    print(f"[OK] Q&A logged to Excel (row {row_num})")
