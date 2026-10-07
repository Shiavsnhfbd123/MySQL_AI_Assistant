from typing import Any

from app.schemas.sql_plan import SQLPlan
from app.services.ai.provider import generate_sql_plan
from app.services.history_service import add_history
from app.services.pending_query_service import (
    claim_pending_query,
    get_pending_query,
    release_pending_query,
    remove_pending_query,
    save_pending_query,
)
from app.services.risk_service import classify_risk, needs_confirmation
from app.services.schema_service import get_database_schema
from app.services.schema_validator import validate_tables
from app.services.sql_executor import execute_sql
from app.services.sql_validator import enforce_read_only, validate_sql


class ConfirmationRequired(ValueError):
    pass


def prepare_query(instruction: str, read_only: bool = False) -> dict[str, Any]:
    schema = get_database_schema()
    plan: SQLPlan = generate_sql_plan(
        instruction=instruction,
        database_schema=schema,
    )
    if plan.needs_clarification:
        return {
            "status": "needs_clarification",
            "explanation": plan.explanation,
            "question": plan.clarification_question,
        }

    validated = validate_sql(plan.sql, plan.parameters)
    validate_tables(validated)
    if read_only:
        enforce_read_only(validated.operation)

    risk = classify_risk(validated)
    confirmation_required = needs_confirmation(risk)
    plan_id = save_pending_query(
        instruction=instruction,
        sql=plan.sql.strip(),
        parameters=plan.parameters,
        operation=validated.operation,
        explanation=plan.explanation,
        risk=risk.value,
        requires_confirmation=confirmation_required,
        read_only=read_only,
        schema_change=validated.schema_change,
    )
    return {
        "status": "prepared",
        "plan_id": plan_id,
        "operation": validated.operation,
        "sql": plan.sql.strip(),
        "parameters": plan.parameters,
        "explanation": plan.explanation,
        "risk": risk.value,
        "requires_confirmation": confirmation_required,
        "executed": False,
    }


def execute_query(plan_id: str, confirm: bool = False) -> dict[str, Any]:
    pending = get_pending_query(plan_id)
    validated = validate_sql(pending["sql"], pending["parameters"])
    validate_tables(validated)
    if pending["read_only"]:
        enforce_read_only(validated.operation)

    current_risk = classify_risk(validated)
    confirmation_required = needs_confirmation(current_risk)
    if confirmation_required and not confirm:
        raise ConfirmationRequired("This operation requires explicit confirmation.")

    pending = claim_pending_query(plan_id)
    try:
        result = execute_sql(pending["sql"], pending["parameters"])
    except Exception as exc:
        release_pending_query(plan_id)
        add_history(
            instruction=pending["instruction"],
            sql=pending["sql"],
            operation=validated.operation,
            risk=current_risk.value,
            success=False,
            affected_rows=None,
            error=str(exc),
        )
        raise

    remove_pending_query(plan_id)
    add_history(
        instruction=pending["instruction"],
        sql=pending["sql"],
        operation=validated.operation,
        risk=current_risk.value,
        success=True,
        affected_rows=result.get("affected_rows", result.get("row_count")),
        error=None,
    )
    return {
        "status": "executed",
        "plan_id": plan_id,
        "operation": validated.operation,
        "risk": current_risk.value,
        "sql": pending["sql"],
        "result": result,
        "schema_changed": pending["schema_change"],
    }


def cancel_query(plan_id: str) -> dict[str, Any]:
    if not remove_pending_query(plan_id):
        raise ValueError("Pending plan was not found or has already expired.")
    return {"status": "cancelled", "plan_id": plan_id}
