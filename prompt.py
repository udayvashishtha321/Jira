from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import json
import re

load_dotenv()

# ─────────────────────────────────────────────
# Model
# ─────────────────────────────────────────────
model = ChatGroq(
   model="llama-3.3-70b-versatile",
   
    temperature=0.2,
)

# ─────────────────────────────────────────────
# Acceptance Criteria Prompt
# ─────────────────────────────────────────────
ac_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are a senior software architect and code review expert, you have experience of about in 20 years in tech related feild and have
a good expertise in software related things
Your task is to generate concise, implementation-focused acceptance criteria for engineering tasks.
Acceptance criteria must:
- Be specific and testable from code review
- Focus on backend/frontend implementation behavior
- Include validation, security, error handling, and expected functionality where relevant
- Avoid vague business language
- Avoid generic statements
- Be useful for an LLM-based PR/code review system
Rules:
- Generate ONLY 4-5 acceptance criteria
- Each criterion must be one sentence
- Keep criteria concise and implementation-oriented
- Do not generate redundant points
- Do not include markdown
- Return output ONLY as a JSON array of strings
Good Example:
[
  "POST /register endpoint is implemented and accepts email and password in request body",
  "Email format and required field validation are implemented",
  "Duplicate email registrations are prevented before user creation",
  "Password is securely hashed before database persistence",
  "API returns appropriate HTTP status codes and sanitized error responses"
]
"""
    ),
    (
        "human",
        """
Task Summary:
{summary}
Task Description:
{description}
Generate implementation-focused acceptance criteria.
"""
    )
])

# ─────────────────────────────────────────────
# Global State
# ─────────────────────────────────────────────
EMAIL = URL = TOKEN = PROJECT = ""
REQ_TEXT = PERSON_TEXT = ""
TEAM_MEMBERS = {}  


# ─────────────────────────────────────────────
# LAYER 0 — PDF Extraction
# ─────────────────────────────────────────────
def extract_pdf_text(uploaded_file) -> str:
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += (page.extract_text() or "") + "\n"
    return text.strip()


# ─────────────────────────────────────────────
# LAYER 0B — Parse Team Members from text
# Returns { "Exact Name": "role" }
# ─────────────────────────────────────────────
def parse_team_members(person_text: str) -> dict:
    prompt = f"""
You are a text parser. Extract ALL team members from the document below.
Return ONLY a valid JSON object like:
{{"Full Name": "their role", "Full Name 2": "their role"}}

Rules:
- Use the EXACT name as written in the document
- Role must be lowercase (e.g. "backend developer", "frontend developer", "tester", "database administrator")
- No explanation, no markdown, no extra text. Just JSON.

DOCUMENT:
{person_text}
"""
    res = model.invoke(prompt)
    raw = res.content.strip()
    raw = re.sub(r"```json|```", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(" Could not parse team members JSON. Raw output:")
        print(raw)
        return {}


# ─────────────────────────────────────────────
# Send Data — call this from your UI/Streamlit
# ─────────────────────────────────────────────
def send_data(email, url, api_token, project_key, req_file, person_file):
    global EMAIL, URL, TOKEN, PROJECT
    global REQ_TEXT, PERSON_TEXT, TEAM_MEMBERS

    EMAIL = email
    URL = url
    TOKEN = api_token
    PROJECT = project_key

    REQ_TEXT = extract_pdf_text(req_file)
    PERSON_TEXT = extract_pdf_text(person_file)
    TEAM_MEMBERS = parse_team_members(PERSON_TEXT)

    print(f"✅ Extracted requirements: {len(REQ_TEXT)} chars")
    print(f"✅ Extracted team members: {TEAM_MEMBERS}")

    return "done"


# ─────────────────────────────────────────────
# LAYER 1 — Build Dynamic Prompt
# ─────────────────────────────────────────────
def build_prompt(req_text: str, team_members: dict, error_feedback: str = "") -> str:
    allowlist = "\n".join(
        [f'  - "{name}" → {role}' for name, role in team_members.items()]
    )

    skill_rules = """
- Assign backend / API / server tasks → backend developer
- Assign UI / frontend / screen tasks → frontend developer
- Assign database / schema / query tasks → database administrator
- Assign testing / QA / test cases tasks → tester
- If multiple people share a role → distribute evenly (round robin)
"""

    correction_block = ""
    if error_feedback:
        correction_block = f"""
⚠️ CORRECTION REQUIRED:
The previous response had these errors. Fix ONLY these issues:
{error_feedback}
"""

    prompt = f"""
You are a Jira task generator. Analyze the requirement document and generate Jira tasks.

{correction_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUIREMENT DOCUMENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{req_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VALID ASSIGNEES (use EXACTLY these names — spelling, spacing, capitalization must match):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{allowlist}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SKILL ASSIGNMENT RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{skill_rules}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRICT RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Return ONLY valid JSON. No markdown. No explanation. No extra text.
2. Every "assignee" value MUST be one of the exact names in the VALID ASSIGNEES list above.
3. Do NOT invent, abbreviate, or modify any name.
4. Every task MUST have "status": "TODO"
5. Generate 1 Epic, multiple Stories, multiple Tasks per Story.

Return this exact structure:
{{
  "project_key": "{PROJECT if PROJECT else 'PROJ'}",
  "epic": {{
    "summary": "...",
    "description": "...",
    "epic_name": "..."
  }},
  "stories": [
    {{
      "summary": "...",
      "description": "...",
      "tasks": [
        {{
          "summary": "...",
          "description": "...",
          "assignee": "EXACT NAME FROM VALID ASSIGNEES",
          "status": "TODO"
        }}
      ]
    }}
  ]
}}
"""
    return prompt


# ─────────────────────────────────────────────
# LAYER 2 — Validate LLM Output
# Returns (is_valid: bool, errors: list[str])
# ─────────────────────────────────────────────
def validate_output(data: dict, team_members: dict) -> tuple[bool, list[str]]:
    errors = []
    valid_names = set(team_members.keys())

    stories = data.get("stories", [])
    if not stories:
        errors.append("No stories found in output.")

    for s_idx, story in enumerate(stories):
        tasks = story.get("tasks", [])
        if not tasks:
            errors.append(f"Story {s_idx+1} '{story.get('summary','')}' has no tasks.")

        for t_idx, task in enumerate(tasks):
            assignee = task.get("assignee", "")
            status = task.get("status", "")

            if assignee not in valid_names:
                errors.append(
                    f"Story {s_idx+1}, Task {t_idx+1}: "
                    f"Invalid assignee '{assignee}'. "
                    f"Must be one of: {list(valid_names)}"
                )

            if status != "TODO":
                errors.append(
                    f"Story {s_idx+1}, Task {t_idx+1}: "
                    f"status must be 'TODO', got '{status}'"
                )

            for field in ["summary", "description", "assignee", "status"]:
                if not task.get(field):
                    errors.append(
                        f"Story {s_idx+1}, Task {t_idx+1}: missing field '{field}'"
                    )

    return (len(errors) == 0), errors


# ─────────────────────────────────────────────
# LAYER 3 — Generate Acceptance Criteria
# Adds "acceptance_criteria" to each task
# ─────────────────────────────────────────────
def generate_acceptance_criteria(task: dict) -> list[str]:
    """
    Calls the LLM with the ac_prompt to generate acceptance criteria
    for a single task. Returns a list of criterion strings.
    """
    chain = ac_prompt | model
    res = chain.invoke({
        "summary": task.get("summary", ""),
        "description": task.get("description", ""),
    })
    raw = res.content.strip()
    raw = re.sub(r"```json|```", "", raw).strip()
    try:
        criteria = json.loads(raw)
        if isinstance(criteria, list):
            return criteria
    except json.JSONDecodeError:
        print(f"⚠️ Could not parse acceptance criteria JSON for task: {task.get('summary')}")
        print(f"   Raw: {raw}")
    return []


def enrich_tasks_with_ac(data: dict) -> dict:
    """
    Iterates over all tasks in all stories and adds
    'acceptance_criteria' to each task dict.
    Final task shape:
    {
      "summary": "...",
      "description": "...",
      "acceptance_criteria": [...],
      "assignee": "...",
      "status": "TODO"
    }
    """
    total_tasks = sum(len(s.get("tasks", [])) for s in data.get("stories", []))
    done = 0

    for story in data.get("stories", []):
        for task in story.get("tasks", []):
            done += 1
            
            ac = generate_acceptance_criteria(task)
            # Insert acceptance_criteria in the desired field order
            enriched = {
                "summary": task.get("summary", ""),
                "description": task.get("description", ""),
                "acceptance_criteria": ac,
                "assignee": task.get("assignee", ""),
                "status": task.get("status", "TODO"),
            }
            task.clear()
            task.update(enriched)

    return data


# ─────────────────────────────────────────────
# LAYER 4 — Main Analyzer with Retry Loop
# ─────────────────────────────────────────────
def analyze_requirement_doc(max_retries: int = 3) -> dict:
    """
    1. Calls the LLM to generate tasks (with retry + validation).
    2. Enriches every task with acceptance criteria.
    Returns the final enriched JSON dict.
    """
    if not REQ_TEXT or not TEAM_MEMBERS:
        raise ValueError("Call send_data() first to load documents.")

    error_feedback = ""

    for attempt in range(1, max_retries + 1):
        print(f"\n Attempt {attempt}/{max_retries} — Generating tasks...")

        prompt = build_prompt(REQ_TEXT, TEAM_MEMBERS, error_feedback)
        res = model.invoke(prompt)
        raw = res.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            error_feedback = f"Response was not valid JSON. Error: {e}. Return ONLY raw JSON."
            print(f" JSON parse failed: {e}")
            continue

        is_valid, errors = validate_output(data, TEAM_MEMBERS)

        if is_valid:
            print(f"✅ Task validation passed on attempt {attempt}!")
            break
        else:
            print(f"❌ Validation failed with {len(errors)} error(s):")
            for err in errors:
                print(f"   • {err}")
            error_feedback = "\n".join(errors)
    else:
        raise RuntimeError(
            f" Failed to generate valid output after {max_retries} attempts. "
            f"Last errors:\n{error_feedback}"
        )

    # Enrich every task with acceptance criteria
    print("\nEnriching tasks with acceptance criteria...")
    data = enrich_tasks_with_ac(data)
    print(" All tasks enriched with acceptance criteria!")

    return data


# ─────────────────────────────────────────────
# Quick test — run this file directly
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing with local PDFs...")

    result = send_data(
        email="aryansaxena1204@gmail.com",
        url="https://aryansaxena1204-1775726337759.atlassian.net",
        api_token="jira token",
        project_key="SCRUM",
        req_file="requirements.pdf",
        person_file="employees.pdf",
    )

    print(f"send_data: {result}")

    output = analyze_requirement_doc()

    print("\n✅ Final Output:")
    print(json.dumps(output, indent=2))