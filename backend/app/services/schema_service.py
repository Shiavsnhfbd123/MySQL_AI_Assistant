from collections import defaultdict
from typing import Any

from app.config import settings
from app.db.connection import get_connection


def get_schema_details() -> dict[str, Any]:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT TABLE_NAME, TABLE_TYPE
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s
            ORDER BY TABLE_NAME
            """,
            (settings.mysql_database,),
        )
        table_rows = cursor.fetchall()
        cursor.execute(
            """
            SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY,
                   COLUMN_DEFAULT, EXTRA, ORDINAL_POSITION
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s
            ORDER BY TABLE_NAME, ORDINAL_POSITION
            """,
            (settings.mysql_database,),
        )
        columns = defaultdict(list)
        for row in cursor.fetchall():
            columns[row["TABLE_NAME"]].append(
                {
                    "name": row["COLUMN_NAME"],
                    "type": row["COLUMN_TYPE"],
                    "nullable": row["IS_NULLABLE"] == "YES",
                    "primary_key": row["COLUMN_KEY"] == "PRI",
                    "default": row["COLUMN_DEFAULT"],
                    "extra": row["EXTRA"] or "",
                }
            )
        cursor.execute(
            """
            SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL
            ORDER BY TABLE_NAME, COLUMN_NAME
            """,
            (settings.mysql_database,),
        )
        foreign_keys = defaultdict(list)
        for row in cursor.fetchall():
            foreign_keys[row["TABLE_NAME"]].append(
                {
                    "column": row["COLUMN_NAME"],
                    "referenced_table": row["REFERENCED_TABLE_NAME"],
                    "referenced_column": row["REFERENCED_COLUMN_NAME"],
                }
            )
        tables = [
            {
                "name": row["TABLE_NAME"],
                "type": row["TABLE_TYPE"],
                "columns": columns[row["TABLE_NAME"]],
                "foreign_keys": foreign_keys[row["TABLE_NAME"]],
            }
            for row in table_rows
        ]
        return {"database": settings.mysql_database, "tables": tables}
    finally:
        cursor.close()
        connection.close()


def get_database_schema() -> str:
    details = get_schema_details()
    if not details["tables"]:
        return "DATABASE CURRENTLY HAS NO TABLES."
    lines: list[str] = []
    for table in details["tables"]:
        lines.append(f"TABLE: {table['name']}")
        foreign_keys = {item["column"]: item for item in table["foreign_keys"]}
        for column in table["columns"]:
            parts = [f"- {column['name']} {column['type']}"]
            if column["primary_key"]:
                parts.append("PRIMARY KEY")
            if not column["nullable"]:
                parts.append("NOT NULL")
            if column["extra"]:
                parts.append(column["extra"])
            if column["name"] in foreign_keys:
                fk = foreign_keys[column["name"]]
                parts.append(f"REFERENCES {fk['referenced_table']}({fk['referenced_column']})")
            lines.append(" ".join(parts))
    return "\n".join(lines)


def get_existing_tables() -> set[str]:
    return {table["name"] for table in get_schema_details()["tables"]}


def get_table_details(table_name: str) -> dict[str, Any]:
    for table in get_schema_details()["tables"]:
        if table["name"] == table_name:
            return table
    raise ValueError(f"Unknown table: {table_name}")
