"""Shared failure behavior until a command has a real implementation."""

from typing import NoReturn

import typer


def not_implemented(command: str) -> NoReturn:
    typer.echo(f"{command} is not implemented yet.", err=True)
    raise typer.Exit(code=1)
