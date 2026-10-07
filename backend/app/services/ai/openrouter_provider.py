import httpx
from pydantic import ValidationError

from app.config import settings
from app.schemas.sql_plan import SQLPlan
from app.services.ai.common import SYSTEM_PROMPT, build_user_prompt, extract_json_object


def generate_with_openrouter(instruction: str, database_schema: str) -> SQLPlan:
    if not instruction.strip():
        raise ValueError("Instruction cannot be blank.")
    if not settings.openrouter_api_key:
        raise RuntimeError(
            "OpenRouter is not configured. Add OPENROUTER_API_KEY to backend/.env."
        )

    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_user_prompt(instruction, database_schema),
            },
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=settings.openrouter_timeout) as client:
            response = client.post(settings.openrouter_url, headers=headers, json=payload)
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise RuntimeError("The AI provider timed out. Please try again.") from exc
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        raise RuntimeError(f"The AI provider rejected the request (HTTP {status}).") from exc
    except httpx.RequestError as exc:
        raise RuntimeError("The AI provider is currently unreachable.") from exc

    try:
        content = response.json()["choices"][0]["message"]["content"]
        return SQLPlan.model_validate(extract_json_object(content))
    except (KeyError, IndexError, TypeError, ValidationError) as exc:
        raise RuntimeError("The AI provider returned an invalid structured plan.") from exc
