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
from ..catalog_skills import resolve_catalog_skill
from ..workspace import open_workspace


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
                      questions: tuple[Question, ...], *, ref: str | None = None) -> str:
    executable = Path(sys.argv[0]).stem
    if executable not in {'pspec', 'powerspec'}:
        executable = 'pspec'
    selector = f'--ref "{ref}"' if ref is not None else f'--path "{selected}"'
    command = f'{executable} resolve skill {selector} --agent {agent}'
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
        "After recording the confirmed value, rerun from the same task directory with the same selector, agent, and change:",
        "",
        f"`{command}`",
    ])
    return "\n".join(lines).rstrip() + "\n"


def skill(
    agent: Annotated[str, typer.Option(help="Invoking agent identifier.")],
    path: Annotated[Path | None, typer.Option(help="Skill location selected by the native integration.")] = None,
    ref: Annotated[str | None, typer.Option(help="Selected catalog skill name or exact resource reference.")] = None,
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
    """Resolve a native-selected path or one selected catalog reference."""
    try:
        cwd = Path.cwd()
        if name is not None or selected is not None:
            raise ConfigurationError(
                'Use pspec resolve skill --path "<native-selected-location>" --agent <agent>; '
                "obtain the path through your native skill integration, not name-based lookup."
            )
        if (path is None) == (ref is None):
            raise ConfigurationError('Supply exactly one of --path "<native-selected-location>" or --ref "<selected-catalog-reference>" and --agent <agent>; native paths come from your native skill integration.')
        if ref is not None:
            with open_workspace(cwd, agent=agent, runtime=True, resolve_skills=False) as workspace:
                resolved = resolve_catalog_skill(workspace, ref, change=change)
                skill_root, name, ref, result = resolved.root, resolved.name, resolved.ref, resolved.resolution
        else:
            skill_root, name = selected_skill(path)
            if not manifest_supported(skill_root):
                typer.echo("null")
                return
            consumer = discover_consumer(cwd)
            with builtin_catalog_root() as root:
                result = resolve_skill(skill_root, _bundle(cwd, agent, consumer, root), consumer, change=change)
        identity = {'skill_ref': ref} if ref is not None else {}
        if result.status == "resolved":
            if json_output:
                typer.echo(json.dumps({
                    "status": "resolved",
                    "skill": name,
                    "skill_path": str(skill_root),
                    **identity,
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
                **identity,
                "agent": agent,
                "change": change,
                "questions": [_question_data(question) for question in result.questions],
            }, ensure_ascii=False))
        else:
            typer.echo(_pending_markdown(name, agent, change, skill_root, result.questions, ref=ref), nl=False)
    except (ConfigurationError, OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error
