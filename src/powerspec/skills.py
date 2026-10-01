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


@dataclass(frozen=True)
class MarkdownSection:
    title: str
    level: int
    start: int
    end: int
    text: str


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


def _strip_frontmatter(text: str, location: Path) -> str:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text
    for index, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            return "".join(lines[index + 1:]).lstrip("\r\n")
    raise ConfigurationError(f"{location}: unterminated frontmatter")


def read_document(path: Path | str, *, root: Path, entrypoint=False) -> str:
    root = Path(root).resolve(strict=True)
    requested = Path(path)
    if requested.anchor or ".." in requested.parts:
        raise ConfigurationError(f"{path}: expected a contained relative file")
    try:
        selected = (root / requested).resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ConfigurationError(f"{root / requested}: selected resource is unavailable: {error}") from error
    if not selected.is_relative_to(root):
        raise ConfigurationError(f"{selected}: selected resource escapes skill root {root}")
    if not selected.is_file():
        raise ConfigurationError(f"{selected}: selected resource is not a file")
    try:
        text = selected.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        raise ConfigurationError(f"{selected}: {error}") from error
    return _strip_frontmatter(text, selected) if entrypoint else text


def _headings(document: str) -> tuple[MarkdownSection, ...]:
    records: list[tuple[str, int, int]] = []
    offset = 0
    fence: tuple[str, int] | None = None
    for line in document.splitlines(keepends=True):
        stripped = line.lstrip()
        marker = re.match(r"(`{3,}|~{3,})", stripped)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = (token[0], len(token))
            elif token[0] == fence[0] and len(token) >= fence[1]:
                fence = None
            offset += len(line)
            continue
        if fence is None:
            found = re.match(r"^(#{1,6})[ \t]+(.+?)[ \t]*\r?\n?$", line)
            if found:
                title = re.sub(r"[ \t]+#+[ \t]*$", "", found.group(2)).strip()
                records.append((title, len(found.group(1)), offset))
        offset += len(line)
    sections: list[MarkdownSection] = []
    for index, (title, level, start) in enumerate(records):
        end = len(document)
        for _, following_level, following_start in records[index + 1:]:
            if following_level <= level:
                end = following_start
                break
        sections.append(MarkdownSection(title, level, start, end, document[start:end]))
    return tuple(sections)


def section(document: str, title: str, *, location: Path | str) -> MarkdownSection:
    matches = [item for item in _headings(document) if item.title == title]
    if not matches:
        raise ConfigurationError(f"{location}: missing Markdown section {title!r}")
    if len(matches) != 1:
        raise ConfigurationError(f"{location}: ambiguous Markdown section {title!r}")
    return matches[0]


def _replace_once(text: str, values: dict[str, Any]) -> str:
    return VARIABLE.sub(lambda match: str(values[match.group(1)])
                        if match.group(1) in values else match.group(0), text)


@dataclass(frozen=True)
class _Material:
    order: int
    dynamic: Dynamic
    target: MarkdownSection
    identity: tuple[Path, str | None]
    content: str


def _materialize(root: Path, item: Dynamic, order: int, target: MarkdownSection,
                 values: dict[str, Any]) -> _Material:
    variables = VARIABLE.findall(item.path)
    missing = [key for key in variables if key not in values]
    if missing:
        raise ConfigurationError(f"dynamic {item.section}: unresolved path variables {missing}")
    relative_text = _replace_once(item.path, values)
    relative = _relative_pattern(relative_text, allow_glob=False)
    try:
        canonical = (root / relative).resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ConfigurationError(f"{root / relative}: selected resource is unavailable: {error}") from error
    source = read_document(relative, root=root)
    if item.source_section is not None:
        source = section(source, item.source_section, location=canonical).text
    source = source.strip()
    label = f"<!-- Source: {relative.as_posix()}"
    if item.source_section is not None:
        label += f", section: {item.source_section}"
    content = f"{label} -->\n{source}\n\n"
    return _Material(order, item, target, (canonical, item.source_section), content)


def compose_document(root: Path, entry: str, dynamics: list[Dynamic] | tuple[Dynamic, ...],
                     values: dict[str, Any]) -> str:
    """Assemble active dynamic entries against stable original coordinates."""
    root = Path(root).resolve(strict=True)
    document = read_document(entry, root=root, entrypoint=True)
    materials: list[_Material] = []
    for order, item in enumerate(dynamics):
        target = section(document, item.section, location=root / entry)
        materials.append(_materialize(root, item, order, target, values))

    replacement_targets = {
        (item.target.start, item.target.end): item.target
        for item in materials if item.dynamic.pos in {"replace", "combine"}
    }

    def suppressed(item: _Material) -> bool:
        for ancestor in replacement_targets.values():
            if ancestor.start < item.target.start < ancestor.end:
                return True
        return False

    eligible = [item for item in materials if not suppressed(item)]
    replacements: dict[int, tuple[int, str]] = {}
    for start, target in sorted((value.start, value) for value in replacement_targets.values()):
        group = [item for item in eligible if item.target.start == start
                 and item.dynamic.pos in {"replace", "combine"}]
        if not group:
            continue
        retained: list[tuple[tuple[Path, str | None], str]] = []
        for item in sorted(group, key=lambda value: value.order):
            if item.dynamic.pos == "replace":
                retained = [(item.identity, item.content)]
            elif item.identity not in {identity for identity, _ in retained}:
                retained.append((item.identity, item.content))
        replacements[start] = (target.end, "".join(content for _, content in retained))

    insertions: dict[int, list[tuple[int, int, int, str]]] = {}
    seen: set[tuple[int, str, tuple[Path, str | None]]] = set()
    for item in eligible:
        if item.dynamic.pos not in {"before", "after"}:
            continue
        key = item.target.start, item.dynamic.pos, item.identity
        if key in seen:
            continue
        seen.add(key)
        position = item.target.start if item.dynamic.pos == "before" else item.target.end
        # Ending child sections precede ending ancestors; after precedes before at a shared endpoint.
        phase = 0 if item.dynamic.pos == "after" else 1
        depth = -item.target.start if item.dynamic.pos == "after" else item.target.start
        insertions.setdefault(position, []).append((phase, depth, item.order, item.content))

    output: list[str] = []
    cursor = 0
    positions = sorted(set(insertions) | set(replacements))
    for position in positions:
        if position < cursor:
            continue
        output.append(document[cursor:position])
        for _, _, _, content in sorted(insertions.get(position, [])):
            output.append(content)
        if position in replacements:
            end, content = replacements[position]
            output.append(content)
            cursor = end
        else:
            cursor = position
    output.append(document[cursor:])
    return _replace_once("".join(output), values).rstrip() + "\n"
