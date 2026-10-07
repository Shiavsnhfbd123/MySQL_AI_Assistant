import json

from app.services.ai import ollama_provider


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
        return {"message": {"role": "assistant", "content": json.dumps(plan)}}


class FakeClient:
    def __init__(self, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def post(self, *args, **kwargs):
        self.payload = kwargs["json"]
        return FakeResponse()


def test_ollama_plan_uses_structured_output(monkeypatch):
    monkeypatch.setattr(ollama_provider.httpx, "Client", FakeClient)
    plan = ollama_provider.generate_with_ollama(
        "give students age more 20",
        "TABLE: students\n- age int",
    )
    assert plan.operation == "SELECT"
    assert plan.parameters == [20]


def test_ollama_repairs_semantically_invalid_plan(monkeypatch):
    invalid = {
        "intent": "list_students",
        "operation": "SELECT",
        "sql": "SELECT * FROM students WHERE age > %s",
        "parameters": [],
        "explanation": "Shows students older than 20.",
        "needs_clarification": False,
        "clarification_question": "",
    }
    valid = {**invalid, "parameters": [20]}

    class RepairClient(FakeClient):
        calls = 0

        def post(self, *args, **kwargs):
            RepairClient.calls += 1
            plan = invalid if RepairClient.calls == 1 else valid
            response = FakeResponse()
            response.json = lambda: {
                "message": {"role": "assistant", "content": json.dumps(plan)}
            }
            return response

    monkeypatch.setattr(ollama_provider.httpx, "Client", RepairClient)
    plan = ollama_provider.generate_with_ollama(
        "give students age more 20",
        "TABLE: students\n- age int",
    )
    assert RepairClient.calls == 2
    assert plan.parameters == [20]


def test_ollama_uses_optional_bearer_token(monkeypatch):
    captured = {}

    class AuthClient(FakeClient):
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(ollama_provider.httpx, "Client", AuthClient)
    monkeypatch.setattr(ollama_provider.settings, "ollama_api_key", "private-token")

    ollama_provider.generate_with_ollama(
        "give students age more 20",
        "TABLE: students\n- age int",
    )

    assert captured["headers"] == {"Authorization": "Bearer private-token"}
