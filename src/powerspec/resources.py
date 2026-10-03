"""Access complete bundled resources from source or an installed distribution."""
from contextlib import contextmanager
from importlib.metadata import PackageNotFoundError, distribution
from importlib.resources import as_file, files
from pathlib import Path
import shutil
import tempfile



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
            yield Path(root)
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
            yield merged
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
