"""Compose the Powerspec command surface."""

import typer

from .flush import flush
from .config import edit as edit_config, profile as config_profile, show as show_config
from .doctor import doctor
from .hook import hook
from .init import init
from .skill import skill
from .state import show as show_state
from .status import status
from .sync import sync
from .upgrade import upgrade
from .workset import app as workset_app

app = typer.Typer(
    help="Profile-driven project guidance and skill resolution.",
    add_completion=False,
    invoke_without_command=True,
    no_args_is_help=False,
)

resolve_app = typer.Typer(help="Resolve agent-facing Powerspec protocols.")
state_app = typer.Typer(help="Inspect and clear temporary consumer state.")
config_app = typer.Typer(
    help="Inspect and update persistent consumer configuration.",
    invoke_without_command=True,
)


@app.callback()
def root(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@config_app.callback()
def config_root(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


app.command()(init)
app.command()(status)
app.command()(sync)
app.command()(upgrade)
app.command()(doctor)
app.add_typer(config_app, name="config")
app.add_typer(state_app, name="state")
app.add_typer(resolve_app, name="resolve")
app.add_typer(workset_app, name="workset")

resolve_app.command(name="skill")(skill)
resolve_app.command(name="hook")(hook)
state_app.command(name="clear")(flush)
state_app.command(name="show")(show_state)
config_app.command(name="show")(show_config)
config_app.command(name="profile")(config_profile)
config_app.command(name="edit")(edit_config)

def main() -> None:
    """Run the same application for either installed console script."""
    app()
