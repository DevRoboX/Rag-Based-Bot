"""
excel/mapper.py — Field → RAG Query Mapper

WHAT IT DOES:
  For each Excel field name (e.g. "Technical Skills"), generates a
  natural language query (e.g. "What are the technical skills?"),
  runs it through the RAG pipeline, and collects the answer.

WHY A QUERY MAP:
  Field names alone (like "Email") may be too short for good retrieval.
  We expand them into full questions so the semantic search finds
  better matching chunks from the resume.

  e.g.  "Email"  →  "What is the email address or contact email?"
        "GPA"    →  "What is the GPA or academic grade?"

  If a field name is not in the predefined map, we auto-generate
  a sensible question: "What is the [field_name]?"
"""

from rag.pipeline import RAGPipeline

# ─── Predefined Query Map ────────────────────────────────────────────────────
# Maps Excel field labels → richer RAG search queries
# Add more entries here as you customize your Excel template

FIELD_QUERY_MAP = {
    # Contact
    "Full Name":              "What is the full name of the person?",
    "Email Address":          "What is the email address or contact email?",
    "Phone Number":           "What is the phone number or mobile number?",
    "Location":               "What is the city, state, or location of the person?",
    "LinkedIn Profile":       "What is the LinkedIn profile URL or handle?",
    "GitHub Profile":         "What is the GitHub profile URL or username?",
    "Portfolio / Website":    "What is the personal website or portfolio URL?",

    # Summary
    "Professional Summary":   "What is the professional summary, objective, or career profile?",
    "Career Objective":       "What is the career objective or professional goal?",

    # Skills
    "Technical Skills":       "What are the technical skills, programming languages, or technologies?",
    "Soft Skills":            "What are the soft skills, interpersonal or communication skills?",
    "Tools & Frameworks":     "What tools, frameworks, or software does the person use?",
    "Programming Languages":  "What programming languages does the person know?",

    # Experience
    "Years of Experience":    "How many total years of professional work experience does the person have?",
    "Current / Last Company": "What is the most recent or current company the person worked at?",
    "Current / Last Role":    "What is the most recent job title or role?",
    "Current / Last Duration":"What was the duration or tenure at the most recent company?",
    "Previous Company":       "What was the previous company before the most recent one?",
    "Previous Role":          "What was the job title at the previous company?",
    "Previous Duration":      "What was the duration at the previous company?",
    "Key Responsibilities":   "What were the key responsibilities, duties, or work done?",
    "Achievements at Work":   "What achievements, accomplishments, or impact at work?",

    # Education
    "Highest Degree":         "What is the highest educational degree or qualification?",
    "University / College":   "What university, college, or institution did the person attend?",
    "Field of Study / Major": "What was the field of study, major, or specialization?",
    "Graduation Year":        "What year did the person graduate or complete their degree?",
    "CGPA / GPA / Percentage":"What is the CGPA, GPA, or academic percentage?",

    # Projects
    "Key Projects":           "What are the major projects or portfolio projects listed?",
    "Project Technologies":   "What technologies or tools were used in projects?",

    # Certifications
    "Certifications":         "What certifications, certificates, or professional credentials are listed?",
    "Online Courses":         "What online courses or training programs are mentioned?",

    # Achievements
    "Awards & Recognition":   "What awards, honors, or recognition has the person received?",
    "Publications":           "Are there any publications, papers, or articles listed?",

    # Languages
    "Languages Known":        "What languages does the person speak or know?",

    # Extra
    "Hobbies / Interests":    "What are the hobbies, interests, or extracurricular activities?",
    "References":             "Are there any references or referees mentioned?",
}


def get_query_for_field(field_name: str) -> str:
    """
    Get the RAG search query for a given Excel field name.

    Looks up the predefined map first; if not found, auto-generates
    a reasonable question from the field name itself.
    """
    if field_name in FIELD_QUERY_MAP:
        return FIELD_QUERY_MAP[field_name]
    # Auto-generate a fallback query
    return f"What is the {field_name.lower()}?"


def fields_to_answers(fields: dict, rag: RAGPipeline) -> dict:
    """
    Run RAG queries for all fields and collect answers.

    Args:
        fields : {field_name: section_name} from excel/reader.py
        rag    : Initialized RAGPipeline instance

    Returns:
        {field_name: answer_string_or_None}
    """
    answers = {}
    total = len(fields)

    for i, (field_name, section) in enumerate(fields.items(), 1):
        query = get_query_for_field(field_name)
        print(f"  [{i}/{total}] '{field_name}' ← querying RAG ...")

        answer = rag.query_for_excel_field(
            field_name=field_name,
            question=query,
        )
        answers[field_name] = answer

        status = f"[OK] {answer[:60]}..." if answer and len(answer) > 60 else (f"[OK] {answer}" if answer else "[!] Not found")
        print(f"         {status}")

    found = sum(1 for v in answers.values() if v)
    print(f"\n[DONE] Result: {found}/{total} fields filled")
    return answers
