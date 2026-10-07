import mysql.connector
from fastapi import APIRouter, HTTPException

from app.services.schema_service import get_schema_details, get_table_details


router = APIRouter(prefix="/api", tags=["schema"])


@router.get("/schema")
def schema():
    try:
        return get_schema_details()
    except mysql.connector.Error as exc:
        raise HTTPException(status_code=503, detail="Unable to read the MySQL schema.") from exc


@router.get("/tables")
def tables():
    details = schema()
    return {"database": details["database"], "tables": [t["name"] for t in details["tables"]]}


@router.get("/tables/{table_name}")
def table(table_name: str):
    try:
        return get_table_details(table_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except mysql.connector.Error as exc:
        raise HTTPException(status_code=503, detail="Unable to read the MySQL schema.") from exc
