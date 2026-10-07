from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


SQLParameter = str | int | float | bool | None
SQLOperation = Literal[
    "SELECT",
    "SHOW",
    "DESCRIBE",
    "EXPLAIN",
    "INSERT",
    "UPDATE",
    "DELETE",
    "CREATE TABLE",
    "ALTER TABLE",
    "DROP TABLE",
    "TRUNCATE",
    "CREATE INDEX",
    "DROP INDEX",
    "CREATE VIEW",
    "DROP VIEW",
]


class SQLPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: str = "database_query"
    operation: SQLOperation = Field(description="Exact SQL operation represented by sql.")
    sql: str = Field(
        default="",
        description="Executable MySQL using %s placeholders for all user values.",
    )
    parameters: list[SQLParameter] = Field(
        default_factory=list,
        description="One JSON scalar for each %s placeholder, in matching order.",
    )
    explanation: str = Field(
        description="Short plain-language summary with no SQL statement."
    )
    needs_clarification: bool = False
    clarification_question: str = ""

    @model_validator(mode="after")
    def validate_plan_shape(self) -> "SQLPlan":
        if self.needs_clarification:
            if self.sql.strip():
                raise ValueError("Clarification plans cannot contain SQL.")
            if not self.clarification_question.strip():
                raise ValueError("Clarification plans must contain a question.")
        elif not self.sql.strip():
            raise ValueError("Executable plans must contain SQL.")
        elif self.sql.count("%s") != len(self.parameters):
            raise ValueError(
                "The number of SQL placeholders must match the number of parameters."
            )
        return self

    @field_validator("operation", mode="before")
    @classmethod
    def normalize_operation(cls, value: object) -> object:
        return value.strip().upper() if isinstance(value, str) else value


class PlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instruction: str = Field(min_length=2, max_length=4000)
    read_only: bool = False

    @field_validator("instruction")
    @classmethod
    def instruction_must_have_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Instruction cannot be blank.")
        return value


class ExecuteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str = Field(min_length=10, max_length=100)
    confirm: bool = False


class CancelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str = Field(min_length=10, max_length=100)
