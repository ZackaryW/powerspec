"""Skill-local manifests and non-interactive input resolution."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Literal
import re

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .catalog import ConfigurationError, read_toml, skill_metadata
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


class SkillInput(ManifestModel):
    id: Nonempty
    type: Literal["string", "boolean", "integer", "float"]
    choices: list[Any] | None = Field(default=None, min_length=1)
    default: Any = None
    when: dict[Nonempty, Any] = Field(default_factory=dict)
    parser: Prompt | None = None

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
        if self.parser is not None and "default" in self.parser.model_fields_set:
            self.validate_value(self.parser.default)
        return self


class Dynamic(ManifestModel):
    section: Nonempty
    pos: Literal["after", "replace"]
    path: Nonempty
    source_section: Nonempty | None = None
    when: dict[Nonempty, Any] = Field(default_factory=dict)


class SkillManifest(ManifestModel):
    version: Literal[2]
    entry: Nonempty
    input: list[SkillInput] = Field(default_factory=list)
    dynamic: list[Dynamic] = Field(default_factory=list)

    @model_validator(mode="after")
    def references(self):
        identifiers = [item.id for item in self.input]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("input ids must be unique")
        by_id = {item.id: item for item in self.input}
        graph: dict[str, list[str]] = {}
        for item in self.input:
            graph[item.id] = list(item.when)
            for dependency, expected in item.when.items():
                if dependency not in by_id:
                    raise ValueError(f"{item.id}: unknown input reference {dependency}")
                by_id[dependency].validate_value(expected)
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
class SkillResolution:
    status: Literal["pending", "resolved"]
    content: str | None
    questions: tuple[Question, ...]
    values: dict[str, Any]
    origins: dict[str, str]


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
        if not path.resolve(strict=True).is_relative_to(path.parent.resolve(strict=True)):
            raise ConfigurationError(f"{path}: manifest escapes skill root")
    except OSError as error:
        raise ConfigurationError(f"{path}: {error}") from error
    data = read_toml(path)
    version = data.get("version") if isinstance(data, dict) else None
    if version != 2:
        raise ConfigurationError(
            f"{path}: unsupported skill manifest version {version!r}; migrate to version 2"
        )
    if "hint" in data:
        raise ConfigurationError(f"{path}: version 2 removed [[hint]] declarations")
    for item in (data["input"] if isinstance(data.get("input"), list) else ()):
        if not isinstance(item, dict):
            continue
        parser = item.get("parser")
        if isinstance(parser, list):
            raise ConfigurationError(
                f"{path}: version 2 permits one prompt parser; use [input.parser]"
            )
        if isinstance(parser, dict) and "default_hint" in parser:
            raise ConfigurationError(f"{path}: version 2 removed parser default_hint")
    for item in (data["dynamic"] if isinstance(data.get("dynamic"), list) else ()):
        if isinstance(item, dict) and item.get("pos") in {"before", "combine"}:
            raise ConfigurationError(
                f"{path}: version 2 removed dynamic position {item['pos']!r}; use 'after' or 'replace'"
            )
    try:
        return SkillManifest.model_validate(data)
    except (ValidationError, ValueError) as error:
        raise ConfigurationError(f"{path}: {error}") from error


def manifest_supported(root: Path) -> bool:
    """Validate metadata only; absence differs from unreadable or broken entries."""
    path = root / "pspec.toml"
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    except OSError as error:
        raise ConfigurationError(f"{path}: {error}") from error
    load_manifest(path)
    return True


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
        parser = declaration.parser
        suggested = None
        has_suggestion = False
        if parser is not None and "default" in parser.model_fields_set:
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
        for item in materials if item.dynamic.pos == "replace"
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
                 and item.dynamic.pos == "replace"]
        if not group:
            continue
        selected = max(group, key=lambda value: value.order)
        replacements[start] = (target.end, selected.content)

    insertions: dict[int, list[tuple[int, int, int, str]]] = {}
    seen: set[tuple[int, str, tuple[Path, str | None]]] = set()
    for item in eligible:
        if item.dynamic.pos != "after":
            continue
        key = item.target.start, item.dynamic.pos, item.identity
        if key in seen:
            continue
        seen.add(key)
        position = item.target.end
        # Ending child sections precede ending ancestors at a shared endpoint.
        phase = 0
        depth = -item.target.start
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


def _active(item: Dynamic, result: InputResult) -> bool | None:
    """Return None while a guard is pending, otherwise its equality result."""
    for key, expected in item.when.items():
        if key not in result.values:
            return None
        if result.values[key] != expected:
            return False
    return True


def _source_text(root: Path, item: Dynamic, values: dict[str, Any]) -> str:
    missing = [key for key in VARIABLE.findall(item.path) if key not in values]
    if missing:
        raise ConfigurationError(f"dynamic {item.section}: unresolved path variables {missing}")
    relative = _relative_pattern(_replace_once(item.path, values), allow_glob=False)
    source = read_document(relative, root=root)
    if item.source_section is not None:
        source = section(source, item.source_section, location=root / relative).text
    return source


def selected_skill(path: Path) -> tuple[Path, str]:
    """Consume caller selection without querying native installation state."""
    requested = Path(path)
    resolved = requested.resolve(strict=True)
    if resolved.is_dir():
        root = resolved
    elif requested.name in {"SKILL.md", "pspec.toml"} and resolved.is_file():
        root = requested.parent.resolve(strict=True)
        if not resolved.is_relative_to(root):
            raise ConfigurationError(f"{requested}: selected file escapes skill root")
    else:
        raise ConfigurationError(f"{requested}: expected a skill directory, SKILL.md, or pspec.toml")
    name, _ = skill_metadata(root / "SKILL.md", root)
    return root, name


def resolve_skill(root: Path, bundle, consumer, *, change: str | None = None) -> SkillResolution:
    """Resolve one located skill without writing answers or other state."""
    root = Path(root).resolve(strict=True)
    manifest_path = root / "pspec.toml"
    manifest = load_manifest(manifest_path)
    declarations = set(manifest.inputs)
    entry = read_document(manifest.entry, root=root, entrypoint=True)
    needed = set(VARIABLE.findall(entry)) & declarations

    # Resolve guard keys in authored order. A known mismatch prevents later
    # guard/path/content inputs in that branch from becoming reachable.
    for item in manifest.dynamic:
        branch_possible = True
        for key, expected in item.when.items():
            needed.add(key)
            current = resolve_inputs(manifest, bundle, consumer, needed=needed, change=change)
            if key not in current.values:
                branch_possible = False
                break
            if current.values[key] != expected:
                branch_possible = False
                break
        if branch_possible:
            needed.update(set(VARIABLE.findall(item.path)) & declarations)

    first = resolve_inputs(manifest, bundle, consumer, needed=needed, change=change)
    active = [item for item in manifest.dynamic if _active(item, first) is True]

    # Source contents can declare additional inputs, but absent/inactive source
    # branches are never read. Path inputs must be answered before inspection.
    for item in active:
        path_keys = set(VARIABLE.findall(item.path)) & declarations
        if not path_keys.issubset(first.values):
            continue
        needed.update(set(VARIABLE.findall(_source_text(root, item, first.values))) & declarations)

    result = resolve_inputs(manifest, bundle, consumer, needed=needed, change=change)
    if result.questions:
        return SkillResolution("pending", None, result.questions, result.values, result.origins)
    required_inactive = needed & result.inactive
    if required_inactive:
        raise ConfigurationError(
            f"active skill content requires inactive inputs: {sorted(required_inactive)}"
        )
    active = [item for item in manifest.dynamic if _active(item, result) is True]
    content = compose_document(root, manifest.entry, active, result.values)
    return SkillResolution("resolved", content, (), result.values, result.origins)
