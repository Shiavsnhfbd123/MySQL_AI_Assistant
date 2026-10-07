from typing import Any

from app.config import settings
from app.db.connection import get_connection


def execute_sql(sql: str, parameters: list[Any]) -> dict[str, Any]:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(sql, tuple(parameters))
        if cursor.with_rows:
            rows = cursor.fetchmany(settings.max_result_rows + 1)
            truncated = len(rows) > settings.max_result_rows
            rows = rows[: settings.max_result_rows]
            connection.rollback()
            return {
                "type": "result_set",
                "columns": list(cursor.column_names),
                "rows": rows,
                "row_count": len(rows),
                "truncated": truncated,
            }

        connection.commit()
        return {
            "type": "affected_rows",
            "affected_rows": max(cursor.rowcount, 0),
            "last_insert_id": cursor.lastrowid,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()
