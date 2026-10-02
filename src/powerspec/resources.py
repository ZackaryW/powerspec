"""Access complete bundled resources from source or an installed distribution."""
from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path



def _checkout_catalog_root() -> Path:
    return Path(__file__).resolve().parents[2] / ".pspec"


@contextmanager
def builtin_catalog_root():
    """Yield the packaged builtin catalog, with an explicit checkout fallback."""
    packaged = files("powerspec").joinpath("_resources", "catalog")
    if packaged.is_dir():
        with as_file(packaged) as root:
            yield Path(root)
        return
    checkout = _checkout_catalog_root()
    if checkout.is_dir():
        yield checkout
        return
    # Keep resource enumeration independent from the runtime parser dependencies.
    from .catalog import ConfigurationError

    raise ConfigurationError("Powerspec builtin catalog is missing from this installation")
