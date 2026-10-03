"""Load one Git-bounded consumer with a use-case-selected source policy."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .catalog import Catalog, ConfigurationError
from .consumer import Consumer, discover_consumer
from .profiles import Bundle, compose
from .resources import builtin_catalog_root
from .sources import SaucepanSources


SourceMode = Literal["lookup", "ensure"]


@dataclass(frozen=True)
class ConsumerWorkspace:
    consumer: Consumer
    catalog: Catalog
    bundle: Bundle
    source_store: object


@contextmanager
def open_workspace(
    cwd: Path,
    *,
    agent: str,
    source_mode: SourceMode = "lookup",
    runtime: bool = False,
    source_store=None,
    resolve_skills: bool = True,
    resolve_remote_skills: bool = True,
):
    """Yield a fully composed workspace and close packaged-resource handles.

    ``lookup`` is read-only with respect to remote materializations. ``ensure``
    may create the Powerspec Saucepan application and acquire missing recipes.
    """
    consumer = discover_consumer(Path(cwd), runtime=runtime)
    if consumer is None:
        raise ConfigurationError("no owning openspec/.pspec/config.toml within this Git repository")
    store = source_store or SaucepanSources(manage_binary=source_mode == "ensure")
    if source_mode == "lookup":
        resolver = store.lookup
    elif source_mode == "ensure":
        resolver = store.ensure
    else:
        raise ValueError(f"unsupported source mode: {source_mode}") from None
    local = consumer.config_path.parent
    sources = {"local": local} if local.is_dir() else {}
    with builtin_catalog_root() as builtin:
        catalog = Catalog(builtin=builtin, sources=sources, git_resolver=resolver)
        bundle = compose(
            catalog,
            consumer.config.profile,
            agent=agent,
            project_root=consumer.git_root,
            exclude_profiles=consumer.config.exclude_profiles,
            resolve_skills=resolve_skills,
            resolve_remote_skills=resolve_remote_skills,
        )
        yield ConsumerWorkspace(consumer, catalog, bundle, store)
