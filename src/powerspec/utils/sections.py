"""Compose labeled text sections under one introduction."""

from __future__ import annotations

from collections.abc import Iterable


def compose_sections(intro: str, sections: Iterable[tuple[str, str | None]], *, heading: str = "###") -> str:
    """Join non-empty ``(label, body)`` sections in order after *intro*.

    Empty bodies are omitted and a repeated label keeps its first section. A
    single remaining section is still labeled so readers know its origin.
    Returns an empty string when no section has content.
    """
    seen: set[str] = set()
    parts = []
    for label, body in sections:
        if not body or label in seen:
            continue
        seen.add(label)
        parts.append(f"{heading} {label}\n\n{body}")
    return "\n\n".join((intro, *parts)) if parts else ""
