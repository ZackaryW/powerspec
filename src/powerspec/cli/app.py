"""Compose the Powerspec command surface."""

import typer

from .flush import flush
from .hook import hook
from .init import init
from .install import install
from .skill import skill
from .sync import sync
from .upgrade import upgrade

app = typer.Typer(
    help="Profile-driven project guidance and skill resolution.",
    add_completion=False,
    invoke_without_command=True,
    no_args_is_help=False,
)


@app.callback()
def root(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


app.command()(init)
app.command()(install)
app.command()(skill)
app.command()(hook)
app.command()(sync)
app.command()(flush)
app.command()(upgrade)


def main() -> None:
    """Run the same application for either installed console script."""
    app()
