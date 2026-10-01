# Skill content resolution

`pspec.toml` version 1 keeps the shared procedure in its entrypoint and declares only typed inputs, optional suggestions, and dynamic additions. It does not enumerate a second static sequence.

```toml
version = 1
entry = "SKILL.md"

[[input]]
id = "language"
type = "string"
choices = ["python", "rust"]

[[input.parser]]
type = "prompt"
prompt = "Which language applies?"
default = "python" # suggestion, not an answer

[[dynamic]]
section = "Red"
pos = "after"
path = "languages/<language>.md"
source_section = "red"
```

An input-level or dynamic `when = { language = "python" }` is an equality guard; every member must match. Known false guards exclude their branch before dependent inputs are requested. Input defaults are effective values at the lowest runtime precedence. Prompt defaults and matching hints are only suggestions in a pending question and never become values or write state.

Repeated top-level `[[hint]]` entries with one `id` form an ordered local group. Version 1 supports `file-exists` with `file_exists` and `folder-exists` with `folder_exists`. A prompt names one scalar `default_hint`; the first matching detector supplies its suggestion. Detectors are evaluated relative to the owning consumer's Git root only when that unresolved prompt is reachable. Explicit/configured values bypass prompting and hint probes. Invalid effective values fail without falling back.

Runtime precedence is caller skill defaults, global-profile defaults, selected-profile defaults, persistent shared/change values, then temporary shared/change values. Change tables participate only when `--change` is explicit. A pending result tells the agent where a confirmed answer may be placed in `current.toml`; lookup never writes the answer. Without an owning consumer, it reports the unresolved choice without inventing a file location.

The Python TDD branch needs `build_tool`, `test_runner`, and `test_command`. A non-Python selection makes those guarded inputs inactive and asks no Python-tooling questions. The reviewed Python profile supplies `uv`, `pytest`, and `uv run pytest` as effective values; their presence describes configuration and does not prove the executable is installed.
