"""Skill-local manifests and non-interactive input resolution."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Literal
import re

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .catalog import ConfigurationError, read_toml
from .consumer import runtime_values
from .models import VALUE_ADAPTERS
from .utils.dependencies import dependency_order


VARIABLE = re.compile(r"<([A-Za-z_][A-Za-z0-9_]*)>")
Nonempty = Annotated[str, Field(min_length=1)]


class ManifestModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class Prompt(ManifestModel):
    type: Literal["prompt"]
    prompt: Nonempty
    default: Any = None
    default_hint: Nonempty | None = None


class SkillInput(ManifestModel):
    id: Nonempty
    type: Literal["string", "boolean", "integer", "float"]
    choices: list[Any] | None = Field(default=None, min_length=1)
    default: Any = None
    when: dict[Nonempty, Any] = Field(default_factory=dict)
    parser: list[Prompt] = Field(default_factory=list)

    def validate_value(self, value: Any) -> Any:
        result = VALUE_ADAPTERS[self.type].validate_python(value, strict=True)
        if self.choices is not None and result not in self.choices:
            raise ValueError(f"{self.id}: value must be one of {self.choices!r}")
        return result

    @model_validator(mode="after")
    def validate_literals(self):
        for choice in self.choices or []:
            VALUE_ADAPTERS[self.type].validate_python(choice, strict=True)
        if "default" in self.model_fields_set:
            self.validate_value(self.default)
        for parser in self.parser:
            if "default" in parser.model_fields_set:
                self.validate_value(parser.default)
        return self


class Hint(ManifestModel):
    id: Nonempty
    type: Literal["file-exists", "folder-exists"]
    file_exists: Nonempty | None = None
    folder_exists: Nonempty | None = None
    value: Any

    @model_validator(mode="after")
    def detector_field(self):
        expected = self.file_exists if self.type == "file-exists" else self.folder_exists
        other = self.folder_exists if self.type == "file-exists" else self.file_exists
        if expected is None or other is not None:
            raise ValueError(f"{self.type} requires only its matching path field")
        _relative_pattern(expected)
        return self

    @property
    def pattern(self) -> str:
        return self.file_exists or self.folder_exists or ""


class Dynamic(ManifestModel):
    section: Nonempty
    pos: Literal["before", "after", "replace", "combine"]
    path: Nonempty
    source_section: Nonempty | None = None
    when: dict[Nonempty, Any] = Field(default_factory=dict)


class SkillManifest(ManifestModel):
    version: Literal[1]
    entry: Nonempty
    input: list[SkillInput] = Field(default_factory=list)
    hint: list[Hint] = Field(default_factory=list)
    dynamic: list[Dynamic] = Field(default_factory=list)

    @model_validator(mode="after")
    def references(self):
        identifiers = [item.id for item in self.input]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("input ids must be unique")
        by_id = {item.id: item for item in self.input}
        hint_ids = {item.id for item in self.hint}
        graph: dict[str, list[str]] = {}
        for item in self.input:
            graph[item.id] = list(item.when)
            for dependency, expected in item.when.items():
                if dependency not in by_id:
                    raise ValueError(f"{item.id}: unknown input reference {dependency}")
                by_id[dependency].validate_value(expected)
            for parser in item.parser:
                if parser.default_hint is not None and parser.default_hint not in hint_ids:
                    raise ValueError(f"{item.id}: unknown hint group {parser.default_hint}")
        for item in self.dynamic:
            for dependency, expected in item.when.items():
                if dependency not in by_id:
                    raise ValueError(f"dynamic {item.section}: unknown input reference {dependency}")
                by_id[dependency].validate_value(expected)
            unknown = set(VARIABLE.findall(item.path)) - set(by_id)
            if unknown:
                raise ValueError(f"dynamic {item.section}: unknown path variables {sorted(unknown)}")
        try:
            dependency_order(identifiers, graph)
        except ValueError as error:
            raise ValueError(str(error)) from error
        _relative_pattern(self.entry, allow_glob=False)
        return self

    @property
    def inputs(self) -> dict[str, SkillInput]:
        return {item.id: item for item in self.input}


@dataclass(frozen=True)
class Question:
    key: str
    type: str
    prompt: str
    choices: tuple[Any, ...]
    suggested: Any = None
    has_suggestion: bool = False
    answer_location: str | None = None
    change: str | None = None


@dataclass(frozen=True)
class InputResult:
    values: dict[str, Any]
    origins: dict[str, str]
    questions: tuple[Question, ...]
    inactive: frozenset[str]


def _relative_pattern(value: str, *, allow_glob=True) -> Path:
    path = Path(value)
    if path.anchor or path == Path(".") or ".." in path.parts or "\x00" in value:
        raise ValueError(f"expected a contained relative path: {value!r}")
    if not allow_glob and any(character in value for character in "*?[]"):
        raise ValueError(f"globs are not supported here: {value!r}")
    return path


def load_manifest(path: Path) -> SkillManifest:
    path = Path(path)
    try:
        return SkillManifest.model_validate(read_toml(path))
    except (ValidationError, ValueError) as error:
        raise ConfigurationError(f"{path}: {error}") from error


def _matches_hint(hint: Hint, root: Path) -> bool:
    root = root.resolve(strict=True)
    matches = root.glob(hint.pattern)
    for candidate in matches:
        resolved = candidate.resolve()
        if not resolved.is_relative_to(root):
            continue
        if hint.type == "file-exists" and resolved.is_file():
            return True
        if hint.type == "folder-exists" and resolved.is_dir():
            return True
    return False


def resolve_inputs(manifest: SkillManifest, bundle, consumer, *, needed, change=None) -> InputResult:
    """Resolve only reachable requested inputs; suggestions never become values."""
    declarations = manifest.inputs
    unknown = set(needed) - set(declarations)
    if unknown:
        raise ConfigurationError(f"unknown required skill inputs: {sorted(unknown)}")
    defaults = {item.id: item.default for item in manifest.input if "default" in item.model_fields_set}
    all_values, all_origins = runtime_values(consumer, bundle, change=change, defaults=defaults)
    values: dict[str, Any] = {}
    origins: dict[str, str] = {}
    questions: dict[str, Question] = {}
    inactive: set[str] = set()
    resolving: set[str] = set()

    def resolve(key: str) -> str:
        if key in values:
            return "value"
        if key in questions:
            return "pending"
        if key in inactive:
            return "inactive"
        if key in resolving:
            raise ConfigurationError(f"input dependency cycle at {key}")
        resolving.add(key)
        declaration = declarations[key]
        for dependency, expected in declaration.when.items():
            state = resolve(dependency)
            if state == "pending":
                resolving.remove(key)
                return "pending"
            if state == "inactive" or values[dependency] != expected:
                inactive.add(key)
                resolving.remove(key)
                return "inactive"
        if key in all_values:
            try:
                values[key] = declaration.validate_value(all_values[key])
            except (ValidationError, ValueError) as error:
                raise ConfigurationError(f"input {key} from {all_origins[key]}: {error}") from error
            origins[key] = all_origins[key]
            resolving.remove(key)
            return "value"
        parser = declaration.parser[0] if declaration.parser else None
        suggested = None
        has_suggestion = False
        if parser is not None and parser.default_hint is not None and consumer is not None:
            for hint in (item for item in manifest.hint if item.id == parser.default_hint):
                if _matches_hint(hint, consumer.git_root):
                    try:
                        suggested = declaration.validate_value(hint.value)
                    except (ValidationError, ValueError) as error:
                        raise ConfigurationError(f"hint {hint.id} suggests invalid {key}: {error}") from error
                    has_suggestion = True
                    break
        if not has_suggestion and parser is not None and "default" in parser.model_fields_set:
            suggested = parser.default
            has_suggestion = True
        location = None
        if consumer is not None:
            suffix = f"#_change.{change}" if change is not None else "#vars"
            location = f"{consumer.config_path.parent / 'current.toml'}{suffix}"
        questions[key] = Question(
            key, declaration.type, parser.prompt if parser else f"Supply {key}",
            tuple(declaration.choices or ()), suggested, has_suggestion, location, change,
        )
        resolving.remove(key)
        return "pending"

    ordered = [item.id for item in manifest.input if item.id in set(needed)]
    for key in ordered:
        resolve(key)
    return InputResult(values, origins, tuple(questions.values()), frozenset(inactive))
