from typing import Any

import httpx
from pydantic import ValidationError

from app.config import settings
from app.schemas.sql_plan import SQLPlan
from app.services.ai.common import SYSTEM_PROMPT, build_user_prompt, extract_json_object


def _endpoint(path: str) -> str:
    return f"{settings.ollama_base_url.rstrip('/')}{path}"


def _headers() -> dict[str, str]:
    if not settings.ollama_api_key:
        return {}
    return {"Authorization": f"Bearer {settings.ollama_api_key}"}


def _request_content(messages: list[dict[str, str]]) -> str:
    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "format": SQLPlan.model_json_schema(),
        "stream": False,
        "keep_alive": settings.ollama_keep_alive,
        "options": {
            "temperature": settings.ollama_temperature,
            "num_ctx": settings.ollama_num_ctx,
            "num_gpu": settings.ollama_num_gpu,
        },
    }
    try:
        with httpx.Client(
            timeout=settings.ollama_timeout,
            headers=_headers(),
        ) as client:
            response = client.post(_endpoint("/api/chat"), json=payload)
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise RuntimeError("Ollama timed out while generating the SQL plan.") from exc
    except httpx.ConnectError as exc:
        raise RuntimeError(
            "Ollama is not running. Start Ollama and ensure its API is available."
        ) from exc
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise RuntimeError(
                f"Ollama model '{settings.ollama_model}' is not installed. "
                f"Run: ollama pull {settings.ollama_model}"
            ) from exc
        raise RuntimeError(
            f"Ollama rejected the generation request (HTTP {exc.response.status_code})."
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError("The local Ollama service is unreachable.") from exc

    try:
        return str(response.json()["message"]["content"])
    except (KeyError, TypeError) as exc:
        raise RuntimeError("Ollama returned an invalid chat response.") from exc


def generate_with_ollama(instruction: str, database_schema: str) -> SQLPlan:
    if not instruction.strip():
        raise ValueError("Instruction cannot be blank.")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_user_prompt(instruction, database_schema),
        },
    ]
    content = _request_content(messages)
    try:
        return SQLPlan.model_validate(extract_json_object(content))
    except (RuntimeError, ValidationError) as first_error:
        repair_messages = [
            *messages,
            {"role": "assistant", "content": content},
            {
                "role": "user",
                "content": (
                    "Correct the JSON plan. It failed validation because: "
                    f"{first_error}. Return only the corrected object. Ensure every %s "
                    "placeholder has one matching parameters item and executable plans "
                    "put the SQL in the sql field."
                ),
            },
        ]
        repaired_content = _request_content(repair_messages)
        try:
            return SQLPlan.model_validate(extract_json_object(repaired_content))
        except (RuntimeError, ValidationError) as exc:
            raise RuntimeError("Ollama returned an invalid structured SQL plan.") from exc


def get_ollama_status() -> dict[str, Any]:
    status: dict[str, Any] = {
        "provider": "ollama",
        "model": settings.ollama_model,
        "configured": False,
        "connected": False,
        "error": None,
        "accelerator": None,
    }
    try:
        with httpx.Client(
            timeout=settings.ollama_health_timeout,
            headers=_headers(),
        ) as client:
            tags_response = client.get(_endpoint("/api/tags"))
            tags_response.raise_for_status()
            models = tags_response.json().get("models", [])
            installed_names = {
                str(item.get("name") or item.get("model") or "") for item in models
            }
            status["connected"] = True
            status["configured"] = settings.ollama_model in installed_names
            if not status["configured"]:
                status["error"] = "model_missing"
                return status

            try:
                running_response = client.get(_endpoint("/api/ps"))
                running_response.raise_for_status()
                for item in running_response.json().get("models", []):
                    name = str(item.get("name") or item.get("model") or "")
                    if name != settings.ollama_model:
                        continue
                    total_size = int(item.get("size") or 0)
                    vram_size = int(item.get("size_vram") or 0)
                    if total_size and vram_size >= total_size * 0.9:
                        status["accelerator"] = "gpu"
                    elif vram_size > 0:
                        status["accelerator"] = "mixed"
                    elif total_size:
                        status["accelerator"] = "cpu"
            except (httpx.HTTPError, TypeError, ValueError):
                pass
    except httpx.ConnectError:
        status["error"] = "service_unreachable"
    except httpx.HTTPError:
        status["error"] = "service_error"
    except (TypeError, ValueError):
        status["error"] = "invalid_response"
    return status
