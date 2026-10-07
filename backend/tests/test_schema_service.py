from app.services import schema_service


def test_empty_schema_is_described(monkeypatch):
    monkeypatch.setattr(
        schema_service,
        "get_schema_details",
        lambda: {"database": "test", "tables": []},
    )
    assert schema_service.get_database_schema() == "DATABASE CURRENTLY HAS NO TABLES."
