# Proposal

## Why

Multi-project Antigravity sessions currently receive one message that combines every consumer's guidance as labeled sections. Work in a workset always targets one project at a time, so combining them is wrong: the agent gets rules for projects it is not touching, and a seven-repository workset reaches about 42,000 characters, near the roughly 45,000-character size at which Antigravity silently drops the message. Guidance must come from exactly one project: the workset default, or the project the agent chooses.

## What Changes

- A session whose listed paths resolve to two or more distinct consumers no longer receives combined guidance.
- With a matching workset default, the message carries only the default project's guidance, plus a list of the session's projects and the command that fetches one other project's guidance on demand.
- Without a default, the message carries no guidance body: only the project list and that command.
- Paths that resolve to a single consumer deliver that consumer's guidance unlabeled, exactly as a single-project session.
- **BREAKING**: per-project sections and the `(default)` section marker are removed from multi-project output.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `antigravity-hook-delivery`: multi-project sessions deliver one project's guidance or a project list, never combined guidance; failure isolation is restated for that shape.
- `workset-default-project`: a matching default selects the only guidance delivered, instead of naming a fallback among sections.

## Impact

- `src/powerspec/cli/hook.py` multi-project dispatch and its message text.
- `tests/test_hook_antigravity.py`, `tests/test_hook_workset_default.py`.
- `docs/hook-delivery.md` Antigravity section and `docs/worksets.md` default member section.
- `utils/sections.py` stays; it remains a generic helper.
