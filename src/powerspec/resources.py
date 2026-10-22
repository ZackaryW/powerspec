"""Access complete bundled resources from source or an installed distribution."""
from contextlib import contextmanager
from contextvars import ContextVar
from importlib.metadata import PackageNotFoundError, distribution
from importlib.resources import as_file, files
from pathlib import Path
import shutil
import tempfile

# Origins are scoped to the resource handle, including nested workspace calls.
_origins = ContextVar('builtin_skill_origins', default=())


@contextmanager
def _origin_scope(root, origins):
    token = _origins.set((*_origins.get(), (Path(root).resolve(), origins)))
    try:
        yield Path(root)
    finally:
        _origins.reset(token)


def durable_skill_root(entry: Path) -> Path:
    """Map a discovered entry to one whole source tree, never a temporary merge."""
    from .catalog import ConfigurationError, skill_metadata
    entry = entry.resolve()
    for catalog, origins in reversed(_origins.get()):
        if not entry.is_relative_to(catalog):
            continue
        if origins is None:
            raise ConfigurationError(f'{entry}: unsupported transient-only skill location; use a filesystem installation')
        relative = entry.relative_to(catalog)
        for origin in origins:
            directory = origin / relative.parent
            if directory.exists():
                original = directory / entry.name
                if not original.is_file():
                    raise ConfigurationError(f'{directory}: incomplete authored skill tree; supply its SKILL.md')
                if skill_metadata(original, directory)[0] != skill_metadata(entry, catalog)[0]:
                    raise ConfigurationError(f'{directory}: skill identity differs from discovered resource')
                return directory.resolve()
        raise ConfigurationError(f'{entry}: no durable complete skill origin')
    return entry.parent



def _checkout_catalog_root() -> Path:
    return Path(__file__).resolve().parents[2] / ".pspec"


def _distribution_catalog_root() -> Path | None:
    """Locate force-included files that live beside an editable installation."""
    try:
        root = distribution("powerspec").locate_file(
            "powerspec/_resources/catalog"
        )
    except PackageNotFoundError:
        return None
    candidate = Path(root)
    return candidate if candidate.is_dir() else None


@contextmanager
def builtin_catalog_root():
    """Yield the packaged builtin catalog, with an explicit checkout fallback."""
    packaged = files("powerspec").joinpath("_resources", "catalog")
    if packaged.is_dir():
        with as_file(packaged) as root:
            origins = (Path(packaged).resolve(),) if isinstance(packaged, Path) else None
            with _origin_scope(root, origins) as located:
                yield located
        return
    checkout = _checkout_catalog_root()
    installed = _distribution_catalog_root()
    if checkout.is_dir() and installed is not None and checkout.resolve() != installed.resolve():
        # Editable installs physically carry force-included upstream files beside
        # site-packages while authored catalog files remain live in the checkout.
        with tempfile.TemporaryDirectory(prefix="powerspec-catalog-") as name:
            merged = Path(name) / "catalog"
            shutil.copytree(installed, merged)
            shutil.copytree(checkout, merged, dirs_exist_ok=True)
            with _origin_scope(merged, (checkout, installed)) as located:
                yield located
        return
    if installed is not None:
        yield installed
        return
    if checkout.is_dir():
        yield checkout
        return
    # Keep resource enumeration independent from the runtime parser dependencies.
    from .catalog import ConfigurationError

    raise ConfigurationError("Powerspec builtin catalog is missing from this installation")
