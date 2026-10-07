from app.db import connection


def test_mysql_url_overrides_individual_connection_fields(monkeypatch):
    monkeypatch.setattr(
        connection.settings,
        "mysql_url",
        "mysql://app%40user:p%40ss@example.mysql.host:3307/production_db",
    )

    options = connection._connection_options()

    assert options["host"] == "example.mysql.host"
    assert options["port"] == 3307
    assert options["user"] == "app@user"
    assert options["password"] == "p@ss"
    assert options["database"] == "production_db"


def test_mysql_url_rejects_non_mysql_scheme(monkeypatch):
    monkeypatch.setattr(
        connection.settings,
        "mysql_url",
        "postgresql://user:password@host/database",
    )

    try:
        connection._connection_options()
    except ValueError as exc:
        assert "mysql://" in str(exc)
    else:
        raise AssertionError("A non-MySQL URL must be rejected.")
