"""Read consumer ownership and scoped values without persisting resolution."""
from dataclasses import dataclass
from pathlib import Path
from stat import S_ISDIR, S_ISREG
from pydantic import ValidationError
from .catalog import ConfigurationError, read_toml, reference
from .models import ConsumerConfig, Variables, Declaration
from .utils.discovery import find_ancestor_file
from .utils.layers import overlay_layers


@dataclass(frozen=True)
class Consumer:
    config_path: Path
    git_root: Path
    config: ConsumerConfig
    current: Variables | None


def find_git_root(cwd: Path) -> Path | None:
    start = Path(cwd).resolve(strict=True)
    if not start.is_dir():
        raise NotADirectoryError(start)
    for directory in (start, *start.parents):
        try:
            mode = (directory / ".git").stat().st_mode
        except FileNotFoundError:
            continue
        if S_ISDIR(mode) or S_ISREG(mode):
            return directory
    return None


def _load(path, model):
    try:
        return model.model_validate(read_toml(path))
    except ValidationError as error:
        raise ConfigurationError(f"{path}: {error}") from error


def discover_consumer(cwd: Path, *, runtime=True) -> Consumer | None:
    start = Path(cwd).resolve(strict=True)
    boundary = find_git_root(start)
    if boundary is None:
        return None
    for directory in (start, *start.parents):
        relative = ".pspec/config.toml" if directory.name == "openspec" else "openspec/.pspec/config.toml"
        path = find_ancestor_file(directory, relative, boundary=directory)
        if path is not None:
            config = _load(path, ConsumerConfig)
            if config.profile is not None:
                reference(config.profile)
            for excluded in config.exclude_profiles:
                reference(excluded)
            current = None
            if runtime:
                current_path = path.parent / "current.toml"
                if not current_path.resolve().is_relative_to(path.parent):
                    raise ConfigurationError(f"{current_path}: temporary state escapes consumer")
                try:
                    current_path.stat()
                except FileNotFoundError:
                    pass
                else:
                    current = _load(current_path, Variables)
            return Consumer(path, boundary, config, current)
        if directory == boundary:
            break
    return None


def runtime_values(consumer, bundle, *, change=None, defaults=None):
    if change is not None and (not isinstance(change, str) or not change.strip()):
        raise ConfigurationError("change must be an explicit nonempty name")
    layers = [("skill defaults", defaults or {}), ("global profiles", bundle.global_defaults),
              ("selected profiles", bundle.selected_defaults)]
    if consumer is not None:
        for path, values in ((consumer.config_path, consumer.config),
                             (consumer.config_path.parent / "current.toml", consumer.current)):
            if values is None:
                continue
            layers.append((f"{path}#vars", values.vars))
            if change is not None:
                layers.append((f"{path}#_change.{change}", values.changes.get(change, {})))
    return overlay_layers(layers)


def context_values(resource, consumer, bundle):
    declarations = [Declaration.model_validate(item) for item in resource.data.get("compiletime", [])]
    defaults = {item.id: item.default for item in declarations if "default" in item.model_fields_set}
    layers = [(f"{resource.ref} declarations", defaults), ("global profiles", bundle.global_defaults),
              ("selected profiles", bundle.selected_defaults)]
    if consumer is not None:
        layers.append((f"{consumer.config_path}#vars", consumer.config.vars))
    values, origins = overlay_layers(layers)
    for item in declarations:
        if item.id not in values:
            raise ConfigurationError(f"{resource.path}: missing required compiletime value {item.id}")
        try:
            values[item.id] = item.validate_value(values[item.id])
        except ValueError as error:
            raise ConfigurationError(f"{resource.path}: {item.id} from {origins[item.id]}: {error}") from error
    return values, origins
