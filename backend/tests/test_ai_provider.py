from app.schemas.sql_plan import SQLPlan
from app.services.ai import provider


def test_dispatches_to_ollama(monkeypatch):
    monkeypatch.setattr(provider.settings, "ai_provider", "ollama")
    monkeypatch.setattr(
        provider,
        "generate_with_ollama",
        lambda instruction, database_schema: SQLPlan(
            operation="SELECT",
            sql="SELECT 1",
            explanation="Test plan.",
        ),
    )
    plan = provider.generate_sql_plan("test", "empty")
    assert plan.operation == "SELECT"


def test_dispatches_to_openrouter(monkeypatch):
    monkeypatch.setattr(provider.settings, "ai_provider", "openrouter")
    monkeypatch.setattr(
        provider,
        "generate_with_openrouter",
        lambda instruction, database_schema: SQLPlan(
            operation="SELECT",
            sql="SELECT 1",
            explanation="Test plan.",
        ),
    )
    plan = provider.generate_sql_plan("test", "empty")
    assert plan.operation == "SELECT"
