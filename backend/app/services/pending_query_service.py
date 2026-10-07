from copy import deepcopy
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Any
from uuid import uuid4

from app.config import settings


_pending_queries: dict[str, dict[str, Any]] = {}
_lock = RLock()


def save_pending_query(**values: Any) -> str:
    plan_id = str(uuid4())
    item = deepcopy(values)
    item["in_progress"] = False
    item["expires_at"] = datetime.now(timezone.utc) + timedelta(
        minutes=settings.pending_plan_expiry_minutes
    )
    with _lock:
        _pending_queries[plan_id] = item
    return plan_id


def get_pending_query(plan_id: str) -> dict[str, Any]:
    with _lock:
        item = _pending_queries.get(plan_id)
        if item is None:
            raise ValueError("Pending plan was not found or has already been used.")
        if datetime.now(timezone.utc) > item["expires_at"]:
            _pending_queries.pop(plan_id, None)
            raise ValueError("Pending plan has expired. Generate a new plan.")
        if item["in_progress"]:
            raise ValueError("This pending plan is already being executed.")
        return deepcopy(item)


def claim_pending_query(plan_id: str) -> dict[str, Any]:
    with _lock:
        item = get_pending_query(plan_id)
        _pending_queries[plan_id]["in_progress"] = True
        return item


def release_pending_query(plan_id: str) -> None:
    with _lock:
        if plan_id in _pending_queries:
            _pending_queries[plan_id]["in_progress"] = False


def remove_pending_query(plan_id: str) -> bool:
    with _lock:
        return _pending_queries.pop(plan_id, None) is not None
