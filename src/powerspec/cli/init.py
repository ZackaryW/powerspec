from typing import Annotated

import typer

from ._placeholder import not_implemented


def init(
    agent: Annotated[str | None, typer.Option(help="Target agent identifier.")] = None,
) -> None:
    """Initialize a project (placeholder; creates or installs nothing)."""
    not_implemented("init")
