from typing import Annotated

import typer

from ._placeholder import not_implemented


def skill(
    name: Annotated[str, typer.Argument(help="Installed skill name.", metavar="NAME")],
    agent: Annotated[str, typer.Option(help="Invoking agent identifier.")],
    change: Annotated[str | None, typer.Option(help="Active change name.")] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Request structured output when implemented.")
    ] = False,
) -> None:
    """Resolve skill content (placeholder; no resolution or null fallback)."""
    not_implemented("skill")
