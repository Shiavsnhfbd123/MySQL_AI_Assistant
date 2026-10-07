import pytest

from app.services.sql_validator import enforce_read_only, validate_sql


def test_accepts_single_parameterized_select():
    result = validate_sql("SELECT * FROM students WHERE age > %s", [20])
    assert result.operation == "SELECT"


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1; DROP TABLE students",
        "GRANT ALL ON *.* TO attacker",
        "CREATE USER attacker IDENTIFIED BY 'x'",
        "SELECT LOAD_FILE('/etc/passwd')",
        "SELECT * FROM mysql.user",
        "DROP DATABASE mysql_ai_lab",
        "SET GLOBAL general_log = 1",
        "SELECT 1 /*! UNION SELECT 2 */",
    ],
)
def test_blocks_prohibited_sql(sql):
    with pytest.raises(ValueError):
        validate_sql(sql, [])


def test_rejects_placeholder_mismatch():
    with pytest.raises(ValueError, match="placeholder"):
        validate_sql("SELECT * FROM students WHERE id = %s", [])


def test_read_only_rejects_write():
    with pytest.raises(ValueError, match="Read-only"):
        enforce_read_only("UPDATE")
