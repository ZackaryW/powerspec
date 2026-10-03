"""Read temporary consumer state without creating it."""

from dataclasses import dataclass
from pathlib import Path

from .catalog import ConfigurationError
from .consumer import discover_consumer


@dataclass(frozen=True)
class StateResult:
    path: Path
    variables: dict
    changes: dict[str, dict]


def read_state(cwd: Path) -> StateResult:
    consumer = discover_consumer(Path(cwd), runtime=True)
    if consumer is None:
        raise ConfigurationError("no owning openspec/.pspec/config.toml within this Git repository")
    path = consumer.config_path.parent / "current.toml"
    if consumer.current is None:
        return StateResult(path, {}, {})
    return StateResult(path, dict(consumer.current.vars), {
        name: dict(values) for name, values in consumer.current.changes.items()
    })
