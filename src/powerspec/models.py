"""Strict authored configuration shapes; resolution policy lives in callers."""
import ast
from typing import Annotated, Any, Literal
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, TypeAdapter, model_validator, field_validator


def _expression(value: str) -> str:
    try:
        ast.parse(value, mode="eval")
    except SyntaxError as error:
        raise ValueError(f"invalid condition: {error.msg}") from error
    return value


Expression = Annotated[str, AfterValidator(_expression)]
Nonempty = Annotated[str, Field(min_length=1)]


class ConfigurationModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class Profile(ConfigurationModel):
    scope: Literal["user", "project"] = "user"
    global_: bool = Field(default=False, alias="global")
    profiles: list[str] = Field(default_factory=list)
    contexts: list[str] = Field(default_factory=list)
    traits: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    exclude_profiles: list[str] = Field(default_factory=list, alias="exclude-profiles")
    vars: dict[str, Any] = Field(default_factory=dict)


class Trait(ConfigurationModel):
    hooks: list[Nonempty] = Field(min_length=1)
    body: str
    when: Expression | None = None


class Attachment(ConfigurationModel):
    body: str
    id: str | None = None
    when: Expression | None = None


class OperationAttachments(ConfigurationModel):
    guidance: list[Attachment] = Field(default_factory=list)


class Attachments(ConfigurationModel):
    context: list[Attachment] = Field(default_factory=list)
    rules: dict[Nonempty, list[Attachment]] = Field(default_factory=dict)
    operations: dict[Nonempty, OperationAttachments] = Field(default_factory=dict)


VALUE_TYPES = {"string": str, "boolean": bool, "integer": int, "float": float}
VALUE_ADAPTERS = {key: TypeAdapter(value) for key, value in VALUE_TYPES.items()}


class Declaration(ConfigurationModel):
    id: Nonempty
    type: Literal["string", "boolean", "integer", "float"]
    default: Any = None
    choices: list[Any] | None = Field(default=None, min_length=1)

    def validate_value(self, value):
        result = VALUE_ADAPTERS[self.type].validate_python(value, strict=True)
        if self.choices is not None and result not in self.choices:
            raise ValueError(f"{self.id}: value must be one of {self.choices!r}")
        return result

    @model_validator(mode="after")
    def check_declared_values(self):
        for choice in self.choices or []:
            VALUE_ADAPTERS[self.type].validate_python(choice, strict=True)
        if "default" in self.model_fields_set:
            self.validate_value(self.default)
        return self


class Context(ConfigurationModel):
    attach: Attachments = Field(default_factory=Attachments)
    compiletime: list[Declaration] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_inputs(self):
        keys = [item.id for item in self.compiletime]
        if len(set(keys)) != len(keys):
            raise ValueError("compiletime ids must be unique")
        return self


class Variables(ConfigurationModel):
    vars: dict[str, Any] = Field(default_factory=dict)
    changes: dict[str, dict[str, Any]] = Field(default_factory=dict, alias="_change")


class ConsumerConfig(Variables):
    profile: str | None = None
    exclude_profiles: list[str] = Field(default_factory=list, alias="exclude-profiles")

    @field_validator("profile", mode="before")
    @classmethod
    def empty_selection(cls, value):
        return None if value == "" else value
