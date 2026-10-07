import json

from app.services.ai import openrouter_provider


class FakeResponse:
    status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        plan = {
            "intent": "list_students",
            "operation": "SELECT",
            "sql": "SELECT * FROM students WHERE age > %s",
            "parameters": [20],
            "explanation": "Shows students older than 20.",
            "needs_clarification": False,
            "clarification_question": "",
        }
        return {"choices": [{"message": {"content": json.dumps(plan)}}]}


class FakeClient:
    def __init__(self, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def post(self, *args, **kwargs):
        return FakeResponse()


def test_openrouter_plan_is_validated(monkeypatch):
    monkeypatch.setattr(openrouter_provider.settings, "openrouter_api_key", "test-key")
    monkeypatch.setattr(openrouter_provider.httpx, "Client", FakeClient)
    plan = openrouter_provider.generate_with_openrouter("students older 20", "TABLE: students")
    assert plan.operation == "SELECT"
    assert plan.parameters == [20]
