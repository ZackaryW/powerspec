"""Portable runtime trait selection and verified native hook adapters."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from collections.abc import Mapping, Sequence
import json

from .catalog import Catalog, ConfigurationError, Resource
from .conditions import Invocation, trait_contributions
from .consumer import discover_consumer
from .profiles import compose


LOGICAL_EVENTS = frozenset({"sessionStart", "afterCompaction"})
HOOK_RUN_JSON_TIMEOUT = 2.0


@dataclass(frozen=True)
class NativeCallback:
    agent: str
    logical_event: str
    native_event: str
    field: str
    accepted: frozenset[str]
    matcher: str

    @property
    def selector(self) -> str:
        return f"{self.agent}:{self.native_event}"

    def accepts(self, payload: Mapping) -> bool:
        return payload.get("hook_event_name") == self.native_event and payload.get(self.field) in self.accepted


# Both hosts provide context through SessionStart. Their PostCompact callbacks
# can run commands, but cannot deliver model context, so compaction restoration
# deliberately uses SessionStart with source=compact.
CALLBACKS = (
    NativeCallback("codex", "sessionStart", "SessionStart", "source",
                   frozenset({"startup", "clear"}), "startup|clear"),
    NativeCallback("codex", "afterCompaction", "SessionStart", "source",
                   frozenset({"compact"}), "compact"),
    NativeCallback("claude", "sessionStart", "SessionStart", "source",
                   frozenset({"startup", "clear", "fork"}), "startup|clear|fork"),
    NativeCallback("claude", "afterCompaction", "SessionStart", "source",
                   frozenset({"compact"}), "compact"),
)


def callback_for(agent: str, logical_event: str) -> NativeCallback:
    if logical_event not in LOGICAL_EVENTS:
        raise ConfigurationError(f"unsupported logical hook event: {logical_event!r}")
    matches = [item for item in CALLBACKS
               if item.agent == agent and item.logical_event == logical_event]
    if not matches:
        raise ConfigurationError(
            f"{agent!r} has no verified context-delivery mapping for {logical_event}"
        )
    return matches[0]


def _expand(selector: str) -> set[NativeCallback]:
    if selector in LOGICAL_EVENTS:
        return {item for item in CALLBACKS if item.logical_event == selector}
    matches = {item for item in CALLBACKS if item.selector == selector}
    if not matches:
        raise ConfigurationError(f"unsupported hook selector: {selector!r}")
    return matches


def selected_callbacks(selectors: Sequence[str]) -> frozenset[NativeCallback]:
    """Expand positives first, then apply exclusions for one trait."""
    positives: set[NativeCallback] = set()
    negatives: set[NativeCallback] = set()
    for raw in selectors:
        if not isinstance(raw, str) or not raw:
            raise ConfigurationError(f"invalid hook selector: {raw!r}")
        excluded = raw.startswith("~")
        selector = raw[1:] if excluded else raw
        if not selector:
            raise ConfigurationError("hook exclusion requires a selector")
        (negatives if excluded else positives).update(_expand(selector))
    return frozenset(positives - negatives)


def matching_traits(traits: Sequence[Resource], callback: NativeCallback) -> tuple[str, ...]:
    result = []
    for trait in traits:
        try:
            selected = selected_callbacks(trait.data["hooks"])
        except ConfigurationError as error:
            raise ConfigurationError(f"{trait.path}: {error}") from error
        if callback in selected:
            result.append(trait.ref)
    return tuple(result)


def validate_payload(callback: NativeCallback, payload: object) -> Path:
    if not isinstance(payload, dict):
        raise ConfigurationError("native hook input must be one JSON object")
    if not callback.accepts(payload):
        raise ConfigurationError(
            f"native payload does not match {callback.logical_event}: expected "
            f"{callback.native_event} with {callback.field} in {sorted(callback.accepted)!r}"
        )
    cwd = payload.get("cwd")
    if not isinstance(cwd, str) or not cwd:
        raise ConfigurationError("native hook input requires a nonempty cwd")
    path = Path(cwd)
    if not path.is_absolute():
        raise ConfigurationError("native hook cwd must be absolute")
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise ConfigurationError(f"native hook cwd is unavailable: {path}: {error}") from error
    if not resolved.is_dir():
        raise ConfigurationError(f"native hook cwd is not a directory: {resolved}")
    return resolved


def dispatch(*, logical_event: str, agent: str, payload: object, catalog: Catalog,
             change: str | None = None, env=None,
             diagnostics: list[str] | None = None) -> str | None:
    """Resolve and evaluate one native callback without writing any state."""
    callback = callback_for(agent, logical_event)
    cwd = validate_payload(callback, payload)
    consumer = discover_consumer(cwd)
    if consumer is None:
        return None
    bundle = compose(
        catalog,
        consumer.config.profile,
        agent=agent,
        project_root=consumer.git_root,
        exclude_profiles=consumer.config.exclude_profiles,
        resolve_remote_skills=False,
    )
    matching = matching_traits(bundle.traits, callback)
    if not matching:
        return None
    contributions = trait_contributions(
        bundle,
        consumer,
        Invocation(cwd, env=env, run_json_timeout=HOOK_RUN_JSON_TIMEOUT),
        matching_refs=matching,
        change=change,
        isolate_probe_failures=True,
        diagnostics=diagnostics,
    )
    bodies = [item.body for item in contributions if item.body]
    return "\n\n".join(bodies) if bodies else None


def serialize(agent: str, logical_event: str, guidance: str | None) -> str | None:
    if guidance is None:
        return None
    callback = callback_for(agent, logical_event)
    if agent not in {"codex", "claude"}:
        raise ConfigurationError(f"{agent!r} has no verified hook response serializer")
    return json.dumps({
        "hookSpecificOutput": {
            "hookEventName": callback.native_event,
            "additionalContext": guidance,
        }
    }, ensure_ascii=False)


def native_document(agent: str) -> dict:
    """Return one generic, consumer-independent user hook fragment."""
    callbacks = [item for item in CALLBACKS if item.agent == agent]
    if not callbacks:
        raise ConfigurationError(f"{agent!r} has no verified Powerspec hook registrations")
    entries = []
    for callback in callbacks:
        command = f"pspec resolve hook {callback.logical_event} --agent {agent}"
        handler = {
            "type": "command",
            "command": command,
            "timeout": 5,
            "statusMessage": (
                "Restoring Powerspec guidance"
                if callback.logical_event == "afterCompaction"
                else "Loading Powerspec guidance"
            ),
        }
        if agent == "codex":
            handler["additionalContextLimit"] = 5000
        entries.append({"matcher": callback.matcher, "hooks": [handler]})
    return {"hooks": {"SessionStart": entries}}
