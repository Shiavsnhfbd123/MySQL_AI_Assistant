import mysql.connector
from fastapi import APIRouter, HTTPException

from app.schemas.sql_plan import CancelRequest, ExecuteRequest, PlanRequest
from app.services.query_service import (
    ConfirmationRequired,
    cancel_query,
    execute_query,
    prepare_query,
)


router = APIRouter(prefix="/api/query", tags=["query"])


@router.post("/plan")
def plan(request: PlanRequest):
    try:
        return prepare_query(request.instruction, request.read_only)
    except mysql.connector.Error as exc:
        raise HTTPException(
            status_code=503,
            detail="The MySQL database is unavailable. Check the backend database configuration.",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/execute")
def execute(request: ExecuteRequest):
    try:
        return execute_query(request.plan_id, request.confirm)
    except ConfirmationRequired as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except mysql.connector.Error as exc:
        message = getattr(exc, "msg", "The query could not be executed.")
        raise HTTPException(status_code=400, detail=f"MySQL execution failed: {message}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/cancel")
def cancel(request: CancelRequest):
    try:
        return cancel_query(request.plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
