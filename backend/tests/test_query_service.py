from app.schemas.sql_plan import SQLPlan
from app.services import query_service


def test_prepare_uses_backend_operation_and_risk(monkeypatch):
    monkeypatch.setattr(query_service, "get_database_schema", lambda: "TABLE: students")
    monkeypatch.setattr(
        query_service,
        "generate_sql_plan",
        lambda **kwargs: SQLPlan(
            intent="delete_all",
            operation="SELECT",
            sql="DELETE FROM students",
            parameters=[],
            explanation="Deletes all students.",
        ),
    )
    monkeypatch.setattr(query_service, "validate_tables", lambda validated: None)
    response = query_service.prepare_query("delete all students")
    assert response["operation"] == "DELETE"
    assert response["risk"] == "CRITICAL"
    assert response["requires_confirmation"] is True


def test_read_only_is_enforced(monkeypatch):
    monkeypatch.setattr(query_service, "get_database_schema", lambda: "TABLE: students")
    monkeypatch.setattr(
        query_service,
        "generate_sql_plan",
        lambda **kwargs: SQLPlan(
            operation="DELETE",
            sql="DELETE FROM students",
            parameters=[],
            explanation="Deletes all students.",
        ),
    )
    monkeypatch.setattr(query_service, "validate_tables", lambda validated: None)
    try:
        query_service.prepare_query("delete all students", read_only=True)
        assert False, "Expected read-only enforcement"
    except ValueError as exc:
        assert "Read-only" in str(exc)
