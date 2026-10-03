"""Resolve installed skill content for one explicit agent."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Annotated, Any
import json

import typer

from ..catalog import Catalog, ConfigurationError
from ..consumer import discover_consumer
from ..installed import installed_skill
from ..profiles import compose
from ..resources import builtin_catalog_root
from ..skills import Question, resolve_skill


def _bundle(cwd: Path, agent: str, consumer, root: Path):
    if consumer is None:
        return SimpleNamespace(selected_defaults={}, global_defaults={})
    catalog = Catalog(builtin=root)
    return compose(
        catalog,
        consumer.config.profile,
        agent=agent,
        project_root=consumer.git_root,
        exclude_profiles=consumer.config.exclude_profiles,
        resolve_remote_skills=False,
    )


def _question_data(question: Question) -> dict[str, Any]:
    data: dict[str, Any] = {
        "key": question.key,
        "type": question.type,
        "prompt": question.prompt,
        "choices": list(question.choices),
        "answer_location": question.answer_location,
    }
    if question.has_suggestion:
        data["suggested"] = question.suggested
    return data


def _pending_markdown(name: str, agent: str, change: str | None, selected: Path | None,
                      questions: tuple[Question, ...]) -> str:
    command = f"pspec skill {name} --agent {agent}"
    if change is not None:
        command += f" --change {change}"
    if selected is not None:
        command += f' --selected "{selected}"'
    lines = [
        "# Powerspec skill resolution pending",
        "",
        f"The installed `{name}` skill needs confirmed configuration before its procedural content can be returned.",
        "",
    ]
    for question in questions:
        lines.extend([f"## `{question.key}`", "", question.prompt, ""])
        lines.append(f"Type: `{question.type}`")
        if question.choices:
            lines.append("Choices: " + ", ".join(f"`{choice}`" for choice in question.choices))
        if question.has_suggestion:
            lines.append(f"Suggested value: `{question.suggested}` (confirm before saving)")
        if question.answer_location is not None:
            lines.append(f"Answer location: `{question.answer_location}`")
        lines.append("")
    lines.extend([
        "After recording the confirmed value, rerun the same agent and change lookup:",
        "",
        f"`{command}`",
    ])
    return "\n".join(lines).rstrip() + "\n"


def skill(
    name: Annotated[str, typer.Argument(help="Installed skill name.", metavar="NAME")],
    agent: Annotated[str, typer.Option(help="Invoking agent identifier.")],
    change: Annotated[str | None, typer.Option(help="Active change name.")] = None,
    selected: Annotated[
        Path | None,
        typer.Option(help="Installed skill directory or SKILL.md path selected by the host."),
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Return a structured result instead of Markdown.")
    ] = False,
) -> None:
    """Resolve a native installed skill through its optional pspec.toml manifest."""
    try:
        cwd = Path.cwd()
        located = installed_skill(agent, name, cwd=cwd, selected=selected)
        if not (located.root / "pspec.toml").is_file():
            typer.echo("null")
            return
        consumer = discover_consumer(cwd)
        with builtin_catalog_root() as root:
            result = resolve_skill(
                located.root,
                _bundle(cwd, agent, consumer, root),
                consumer,
                change=change,
            )
        if result.status == "resolved":
            if json_output:
                typer.echo(json.dumps({
                    "status": "resolved",
                    "skill": name,
                    "agent": agent,
                    "change": change,
                    "content": result.content,
                }, ensure_ascii=False))
            else:
                typer.echo(result.content, nl=False)
            return
        if json_output:
            typer.echo(json.dumps({
                "status": "pending",
                "skill": name,
                "agent": agent,
                "change": change,
                "questions": [_question_data(question) for question in result.questions],
            }, ensure_ascii=False))
        else:
            typer.echo(_pending_markdown(name, agent, change, selected, result.questions), nl=False)
    except (ConfigurationError, OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error
