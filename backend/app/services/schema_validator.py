from sqlglot import exp

from app.services.schema_service import get_existing_tables
from app.services.sql_validator import ValidatedSQL


def validate_tables(validated: ValidatedSQL) -> None:
    expression = validated.expression
    existing = {name.lower() for name in get_existing_tables()}
    referenced = {
        table.name.lower()
        for table in expression.find_all(exp.Table)
        if table.name
    }
    cte_names = {
        cte.alias_or_name.lower()
        for cte in expression.find_all(exp.CTE)
        if cte.alias_or_name
    }
    referenced -= cte_names

    if validated.operation == "CREATE TABLE":
        target = getattr(expression.this, "name", "")
        if target:
            referenced.discard(target.lower())

    missing = referenced - existing
    if missing:
        raise ValueError("Unknown table(s): " + ", ".join(sorted(missing)))
