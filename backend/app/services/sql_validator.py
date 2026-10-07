import re
from dataclasses import dataclass
from typing import Any

import sqlglot
from sqlglot import exp

from app.config import settings


SYSTEM_SCHEMAS = {"mysql", "performance_schema", "sys", "information_schema"}
READ_ONLY_OPERATIONS = {"SELECT", "SHOW", "DESCRIBE", "EXPLAIN"}
BLOCKED_START = re.compile(
    r"^\s*(GRANT|REVOKE|CREATE\s+USER|ALTER\s+USER|DROP\s+USER|RENAME\s+USER|"
    r"CREATE\s+DATABASE|DROP\s+DATABASE|USE|SET|SHUTDOWN|KILL|FLUSH|RESET|"
    r"INSTALL\s+PLUGIN|UNINSTALL\s+PLUGIN|LOAD\s+DATA|LOCK\s+TABLES|UNLOCK\s+TABLES)\b",
    re.IGNORECASE,
)
BLOCKED_ANYWHERE = re.compile(
    r"\b(INTO\s+OUTFILE|INTO\s+DUMPFILE|LOAD_FILE\s*\(|BENCHMARK\s*\(|SLEEP\s*\()",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ValidatedSQL:
    expression: Any
    operation: str
    schema_change: bool


def _operation_for(expression: Any, sql: str) -> str:
    if isinstance(expression, exp.Select):
        return "SELECT"
    if isinstance(expression, exp.Insert):
        return "INSERT"
    if isinstance(expression, exp.Update):
        return "UPDATE"
    if isinstance(expression, exp.Delete):
        return "DELETE"
    if isinstance(expression, exp.Create):
        return f"CREATE {str(expression.args.get('kind') or '').upper()}".strip()
    if isinstance(expression, exp.Alter):
        return "ALTER TABLE"
    if isinstance(expression, exp.Drop):
        return f"DROP {str(expression.args.get('kind') or '').upper()}".strip()
    if hasattr(exp, "TruncateTable") and isinstance(expression, exp.TruncateTable):
        return "TRUNCATE"

    first = re.match(r"^\s*([A-Z]+)(?:\s+([A-Z]+))?", sql, re.IGNORECASE)
    if first:
        word = first.group(1).upper()
        if word == "SHOW":
            return "SHOW"
        if word in {"DESCRIBE", "DESC"}:
            return "DESCRIBE"
        if word == "EXPLAIN":
            return "EXPLAIN"
        if word == "TRUNCATE":
            return "TRUNCATE"
    raise ValueError("This SQL operation is not supported.")


def validate_sql(sql: str, parameters: list[Any]) -> ValidatedSQL:
    if not sql or not sql.strip():
        raise ValueError("SQL is empty.")
    if len(sql) > 50_000:
        raise ValueError("SQL is too large.")
    if "/*!" in sql:
        raise ValueError("Executable SQL comments are not allowed.")

    placeholder_count = len(re.findall(r"(?<!%)%s", sql))
    if placeholder_count != len(parameters):
        raise ValueError("SQL placeholder count does not match the parameter count.")
    if BLOCKED_START.search(sql) or BLOCKED_ANYWHERE.search(sql):
        raise ValueError("This SQL operation is blocked by backend security rules.")

    sql_for_parsing = re.sub(r"(?<!%)%s", "NULL", sql)
    try:
        statements = [item for item in sqlglot.parse(sql_for_parsing, read="mysql") if item]
    except sqlglot.errors.ParseError as exc:
        raise ValueError(f"Invalid MySQL syntax: {exc}") from exc
    if len(statements) != 1:
        raise ValueError("Only one SQL statement is allowed.")

    expression = statements[0]
    operation = _operation_for(expression, sql)
    allowed = {
        "SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "INSERT", "UPDATE", "DELETE",
        "CREATE TABLE", "CREATE INDEX", "CREATE VIEW", "ALTER TABLE", "DROP TABLE",
        "DROP INDEX", "DROP VIEW", "TRUNCATE",
    }
    if operation not in allowed:
        raise ValueError(f"Operation {operation or 'UNKNOWN'} is not allowed.")

    for table in expression.find_all(exp.Table):
        database = (table.db or "").lower()
        if database in SYSTEM_SCHEMAS:
            raise ValueError("Access to MySQL system schemas is not allowed.")
        if database and database != settings.mysql_database.lower():
            raise ValueError("Cross-database access is not allowed.")

    schema_change = operation in {
        "CREATE TABLE", "CREATE INDEX", "CREATE VIEW", "ALTER TABLE",
        "DROP TABLE", "DROP INDEX", "DROP VIEW", "TRUNCATE",
    }
    return ValidatedSQL(expression=expression, operation=operation, schema_change=schema_change)


def enforce_read_only(operation: str) -> None:
    if operation not in READ_ONLY_OPERATIONS:
        raise ValueError("Read-only mode allows only SELECT, SHOW, DESCRIBE, and EXPLAIN.")
