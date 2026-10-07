from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from uuid import uuid4


_history: deque[dict[str, Any]] = deque(maxlen=200)
_lock = RLock()


def add_history(**values: Any) -> dict[str, Any]:
    item = {
        "id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **deepcopy(values),
    }
    with _lock:
        _history.appendleft(item)
    return deepcopy(item)


def list_history(limit: int = 50) -> list[dict[str, Any]]:
    with _lock:
        return deepcopy(list(_history)[: max(1, min(limit, 200))])
