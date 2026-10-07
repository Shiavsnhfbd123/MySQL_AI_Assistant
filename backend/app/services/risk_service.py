from enum import Enum

from sqlglot import exp

from app.services.sql_validator import ValidatedSQL


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def classify_risk(validated: ValidatedSQL) -> RiskLevel:
    expression = validated.expression
    operation = validated.operation

    if operation in {"SELECT", "SHOW", "DESCRIBE", "EXPLAIN"}:
        return RiskLevel.LOW
    if operation in {"INSERT", "CREATE TABLE", "CREATE INDEX", "CREATE VIEW"}:
        return RiskLevel.MEDIUM
    if operation == "UPDATE":
        return RiskLevel.CRITICAL if expression.args.get("where") is None else RiskLevel.HIGH
    if operation == "DELETE":
        return RiskLevel.CRITICAL if expression.args.get("where") is None else RiskLevel.HIGH
    if operation in {"DROP TABLE", "TRUNCATE"}:
        return RiskLevel.CRITICAL
    if operation in {"ALTER TABLE", "DROP INDEX", "DROP VIEW"}:
        return RiskLevel.HIGH
    return RiskLevel.HIGH


def needs_confirmation(risk: RiskLevel) -> bool:
    return risk in {RiskLevel.HIGH, RiskLevel.CRITICAL}
