import pytest

from app.services.risk_service import RiskLevel, classify_risk, needs_confirmation
from app.services.sql_validator import validate_sql


@pytest.mark.parametrize(
    ("sql", "parameters", "expected"),
    [
        ("SELECT * FROM students", [], RiskLevel.LOW),
        ("INSERT INTO students(name) VALUES (%s)", ["Rahul"], RiskLevel.MEDIUM),
        ("UPDATE students SET age = %s WHERE id = %s", [21, 5], RiskLevel.HIGH),
        ("UPDATE students SET age = %s", [21], RiskLevel.CRITICAL),
        ("DELETE FROM students WHERE id = %s", [5], RiskLevel.HIGH),
        ("DELETE FROM students", [], RiskLevel.CRITICAL),
        ("DROP TABLE students", [], RiskLevel.CRITICAL),
        ("TRUNCATE TABLE students", [], RiskLevel.CRITICAL),
    ],
)
def test_risk_matrix(sql, parameters, expected):
    risk = classify_risk(validate_sql(sql, parameters))
    assert risk == expected
    assert needs_confirmation(risk) is (risk in {RiskLevel.HIGH, RiskLevel.CRITICAL})
