"""
excel/reader.py — Excel Template Reader

WHAT IT DOES:
  Reads the Excel template and extracts the field names (Column A)
  that need to be filled. Also supports extracting fields for a
  specific section (e.g., only "skills" fields).

TEMPLATE FORMAT:
  The Excel template has this structure:

  | Row | Column A (Field Label)    | Column B (Answer) |
  |-----|---------------------------|-------------------|
  |  1  | SECTION: Contact Info     |                   |  ← section header
  |  2  | Full Name                 |                   |  ← field row
  |  3  | Email Address             |                   |
  |  4  | Phone Number              |                   |
  |  5  | SECTION: Skills           |                   |  ← next section
  |  6  | Technical Skills          |                   |
  ...

  Rows starting with "SECTION:" are treated as section headers.
  All other non-empty rows in Column A are field names.

WHY openpyxl:
  - Pure Python — no Microsoft Excel installation needed
  - Read AND write .xlsx files
  - Preserves formatting (colors, fonts) when writing
"""

import openpyxl
from pathlib import Path


SECTION_PREFIX = "SECTION:"


def get_all_fields(template_path: str) -> dict:
    """
    Read ALL field names from the Excel template.

    Returns:
        dict mapping field_name → section_name
        e.g. {"Full Name": "Contact Info", "Technical Skills": "Skills", ...}
    """
    wb = openpyxl.load_workbook(template_path)
    ws = wb.active

    fields = {}
    current_section = "General"

    for row in ws.iter_rows(min_row=1, values_only=True):
        cell_a = str(row[0]).strip() if row[0] else ""

        if not cell_a or cell_a == "None":
            continue

        if cell_a.upper().startswith(SECTION_PREFIX):
            # This is a section header — update current section
            current_section = cell_a[len(SECTION_PREFIX):].strip()
        else:
            # This is a field name — record it under current section
            fields[cell_a] = current_section

    print(f"[OK] Found {len(fields)} fields across {len(set(fields.values()))} sections")
    return fields


def get_section_fields(template_path: str, section_name: str) -> dict:
    """
    Read ONLY the fields belonging to a specific section.

    Args:
        template_path: Path to the Excel template
        section_name:  Section to filter by (case-insensitive partial match)

    Returns:
        dict mapping field_name → section_name (filtered)
    """
    all_fields = get_all_fields(template_path)

    filtered = {
        field: section
        for field, section in all_fields.items()
        if section_name.lower() in section.lower()
    }

    if not filtered:
        print(f"[!] No fields found for section: '{section_name}'")
    else:
        print(f"[OK] Found {len(filtered)} fields in section '{section_name}'")

    return filtered
