"""Resolve content at the caller's native-selected skill location."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Annotated, Any
import json
import sys

import typer

from ..catalog import Catalog, ConfigurationError
from ..consumer import discover_consumer
from ..profiles import compose
from ..resources import builtin_catalog_root
from ..skills import Question, manifest_supported, resolve_skill, selected_skill


def _bundle(cwd: Path, agent: str, consumer, root: Path):
    if consumer is None:
        return SimpleNamespace(selected_defaults={}, global_defaults={})
    catalog = Catalog(builtin=root, sources={'local': consumer.config_path.parent})
    return compose(
        catalog,
        consumer.config.profile,
        agent=agent,
        project_root=consumer.git_root,
        exclude_profiles=consumer.config.exclude_profiles,
        resolve_skills=False,
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


def _pending_markdown(name: str, agent: str, change: str | None, selected: Path,
                      questions: tuple[Question, ...]) -> str:
    executable = Path(sys.argv[0]).stem
    if executable not in {'pspec', 'powerspec'}:
        executable = 'pspec'
    command = f'{executable} resolve skill --path "{selected}" --agent {agent}'
    if change is not None:
        command += f" --change {change}"
    lines = [
        "# Powerspec skill resolution pending",
        "",
        f"The selected `{name}` skill needs confirmed configuration before its procedural content can be returned.",
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
        "After recording the confirmed value, rerun with the same path, agent, and change:",
        "",
        f"`{command}`",
    ])
    return "\n".join(lines).rstrip() + "\n"


def skill(
    agent: Annotated[str, typer.Option(help="Invoking agent identifier.")],
    path: Annotated[Path | None, typer.Option(help="Skill location selected by the native integration.")] = None,
    name: Annotated[str | None, typer.Argument(hidden=True)] = None,
    change: Annotated[str | None, typer.Option(help="Active change name.")] = None,
    selected: Annotated[
        Path | None,
        typer.Option(hidden=True),
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Return a structured result instead of Markdown.")
    ] = False,
) -> None:
    """Assemble content at a native-selected skill path; never discover installations."""
    try:
        cwd = Path.cwd()
        if name is not None or selected is not None or path is None:
            raise ConfigurationError(
                'Use pspec resolve skill --path "<native-selected-location>" --agent <agent>; '
                "obtain the path through your native skill integration, not name-based lookup."
            )
        skill_root, name = selected_skill(path)
        if not manifest_supported(skill_root):
            typer.echo("null")
            return
        consumer = discover_consumer(cwd)
        with builtin_catalog_root() as root:
            result = resolve_skill(
                skill_root,
                _bundle(cwd, agent, consumer, root),
                consumer,
                change=change,
            )
        if result.status == "resolved":
            if json_output:
                typer.echo(json.dumps({
                    "status": "resolved",
                    "skill": name,
                    "skill_path": str(skill_root),
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
                "skill_path": str(skill_root),
                "agent": agent,
                "change": change,
                "questions": [_question_data(question) for question in result.questions],
            }, ensure_ascii=False))
        else:
            typer.echo(_pending_markdown(name, agent, change, skill_root, result.questions), nl=False)
    except (ConfigurationError, OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error
