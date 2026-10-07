from fastapi import APIRouter, Query

from app.services.history_service import list_history


router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history")
def history(limit: int = Query(default=50, ge=1, le=200)):
    return {"items": list_history(limit)}
