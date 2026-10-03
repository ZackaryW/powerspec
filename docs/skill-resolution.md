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

Dynamic entries select an exact, unique Markdown heading from the shared entrypoint. A selected heading includes its body and descendant headings through the next heading at the same or a higher level. Headings inside fenced code blocks are ignored. Omitting `source_section` selects the whole source file.

`before` and `after` retain the shared section and add selected content around it. `replace` replaces the shared section and resets earlier replacement content at that destination. `combine` also replaces the shared section, then appends to the current replacement set; a first `combine` therefore does not keep the original section. A later `replace` wins and clears the retained-source history. Replacement of an ancestor suppresses all dynamic operations aimed inside that original ancestor.

All destinations use the original entrypoint's section coordinates. Inserted content is never searched for new anchors. Duplicate selected sources are removed only when their canonical destination, position, file, and optional source section are equal, so one source can still appear at distinct destinations. Source labels identify the selected relative file and section.

Declared `<name>` values are substituted once after assembly. Values introduced by substitution are not interpreted again, and undeclared angle-bracket prose remains literal. Dynamic path selection must resolve inside the skill root; missing files, ambiguous sections, path escapes, and symlink escapes fail the entire resolution without partial output. The manifest does not need a static sequence, inline markers, the old `after` field, or numbered insertion positions.

## Command outcomes

Run `pspec resolve skill <name> --agent <agent>` or its `powerspec` alias. Add `--change <name>` only when resolving an explicit OpenSpec change, `--selected <installed-path>` when the host reports which native copy it loaded, and `--json` for structured output. The hidden top-level `skill` form remains a compatibility alias.

- `null` means ZuAT located the skill selected by that agent and the installed copy has no `pspec.toml`. The agent follows the ordinary installed skill.
- A pending result contains typed questions, allowed choices, unpersisted suggestions, and the exact shared or change-scoped `current.toml` answer location. It withholds procedural content. Record only a confirmed answer, then rerun the same agent/change/selected-path command.
- A resolved result is assembled Markdown by default. JSON returns `status = resolved` and the identical Markdown in `content`.
- Lookup ambiguity, unsupported agents, invalid selected evidence, malformed manifests, invalid configured values, missing active resources, and ambiguous sections are errors on stderr with a nonzero exit. They never fall back to normal skill handling and never emit a success payload.

Installed lookup is a read-only call to ZuAT for one explicit agent. Powerspec does not observe, register, install, enable, disable, or choose between coexisting native copies. If the `pspec` executable itself is unavailable, the bootstrap skill tells the agent to report that limitation and use the installed skill normally; a malformed manifest is a different case and remains an error.
