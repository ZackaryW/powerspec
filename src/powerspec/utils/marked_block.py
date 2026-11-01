"""Replace one marked block of lines inside text owned by someone else."""

from __future__ import annotations


def split_marked_block(text: str, start: str, end: str) -> tuple[str, str | None, str]:
    """Return ``(before, block_body_or_None, after)`` for the lines between *start* and *end*.

    Markers are whole lines. Raises ``ValueError`` for a marker without its
    partner, a repeated marker, or an end before the start.
    """
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.rstrip('\r\n') == start]
    ends = [i for i, line in enumerate(lines) if line.rstrip('\r\n') == end]
    if not starts and not ends:
        return text, None, ''
    if len(starts) != 1 or len(ends) != 1 or ends[0] < starts[0]:
        raise ValueError(f'malformed managed block: expected one {start!r} followed by one {end!r}')
    first, last = starts[0], ends[0]
    return ''.join(lines[:first]), ''.join(lines[first + 1:last]), ''.join(lines[last + 1:])


def replace_marked_block(text: str, start: str, end: str, body: str) -> str:
    """Put *body* between the markers, appending a new block when none exists.

    Everything outside the markers is preserved byte for byte.
    """
    before, existing, after = split_marked_block(text, start, end)
    block = f'{start}\n{body.rstrip(chr(10))}\n{end}\n'
    if existing is None:
        separator = '' if not text or text.endswith('\n\n') else ('\n' if text.endswith('\n') else '\n\n')
        return text + separator + block
    return before + block + after
