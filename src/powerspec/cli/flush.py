from typing import Annotated

import typer

from ._placeholder import not_implemented


def flush(
    change: Annotated[str | None, typer.Option(help="Change whose temporary values to clear.")] = None,
) -> None:
    """Clear temporary variables (placeholder; preserves all state)."""
    not_implemented("flush")
