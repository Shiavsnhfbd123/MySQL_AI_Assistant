import json
import re
from typing import Any


SYSTEM_PROMPT = """You are the SQL planning component of a secure MySQL assistant.
Convert informal, incomplete, misspelled, or broken English into exactly one MySQL statement.
Use only tables and columns present in the supplied current schema. Never invent schema objects.
Use %s placeholders for every user-provided value and put those values in the parameters array.
There must be exactly one parameters item for each %s placeholder, in the same order.
Example: "students older than 20" becomes sql "SELECT * FROM students WHERE age > %s"
with parameters [20]. Never copy a user-provided literal directly into sql.
Never emit credentials, comments, multiple statements, administrative/server commands,
user or privilege management, database management, file access, or system-schema access.
If the request is ambiguous, set needs_clarification true, keep sql empty, and ask one
short clarification question. Return only an object matching the supplied JSON schema.
For every non-ambiguous request, put the executable statement in the sql field. The sql
field may be empty only when needs_clarification is true. Put only a short plain-language
summary in explanation; never put the SQL statement in explanation.
Do not decide risk or confirmation; the backend calculates both independently."""


def build_user_prompt(instruction: str, database_schema: str) -> str:
    return (
        f"CURRENT DATABASE SCHEMA:\n{database_schema}\n\n"
        f"USER INSTRUCTION:\n{instruction}"
    )


def extract_json_object(content: str) -> dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.I)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RuntimeError("The AI provider returned an invalid structured plan.") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("The AI provider returned an invalid structured plan.")
    return parsed
