from typing import Annotated

import typer

from ._placeholder import not_implemented


def hook(
    event: Annotated[str, typer.Argument(help="Hook event name.", metavar="EVENT")],
) -> None:
    """Dispatch hook guidance (placeholder; emits no guidance)."""
    not_implemented("hook")
