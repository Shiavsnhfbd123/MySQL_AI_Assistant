from typing import Any

from app.config import settings
from app.schemas.sql_plan import SQLPlan
from app.services.ai.ollama_provider import generate_with_ollama, get_ollama_status
from app.services.ai.openrouter_provider import generate_with_openrouter


def generate_sql_plan(instruction: str, database_schema: str) -> SQLPlan:
    if settings.normalized_ai_provider == "ollama":
        return generate_with_ollama(instruction, database_schema)
    return generate_with_openrouter(instruction, database_schema)


def get_ai_status() -> dict[str, Any]:
    if settings.normalized_ai_provider == "ollama":
        return get_ollama_status()
    configured = bool(settings.openrouter_api_key)
    return {
        "provider": "openrouter",
        "model": settings.openrouter_model,
        "configured": configured,
        "connected": configured,
        "error": None if configured else "api_key_missing",
        "accelerator": None,
    }
