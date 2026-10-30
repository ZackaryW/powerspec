# Design

## Context

Hook delivery has three Powerspec-owned pieces in `src/powerspec/hooks.py` and `cli/hook.py`: the `CALLBACKS` table (agent, logical event, native event, matcher), `serialize()` (native response envelope), and `native_document()` (the generic registration ZuAT installs). `provisioning.provision_hooks` is agent-neutral: it writes the document as `powerspec.json` and relies on ZuAT classifications. Today only `codex` and `claude` have callbacks, and `pspec resolve hook` discovers the consumer from `Path.cwd()` and never touches stdin. A past hang when a host left stdin open is why that rule is absolute and tested (`tests/test_hook_input.py`).

Antigravity differs (agy 1.4.10 bundled guide; not yet run-verified): hooks live in a name-keyed `hooks.json`; `SessionStart` is a flat handler list with no matcher and fires once per new conversation; context returns as `injectSteps`; the command runs with its working directory set to the folder containing `hooks.json`; the session context (`workspacePaths`, `conversationId`, `lastUserInput`, ...) arrives as camelCase JSON on stdin. ZuAT's managing of the keyed document is specified in the Zuat change `add-antigravity-agent`. See `proposal.md` for motivation.

## Goals / Non-Goals

**Goals:**
- `pspec init --agent antigravity` installs skills and a working session-start dispatcher; a new Antigravity conversation in a consumer receives its trait guidance.
- Codex and Claude behavior, including never reading stdin by default, stays byte-for-byte the same and still guarded by the existing tests.
- Antigravity hook failures never break the user's session for payload reasons.

**Non-Goals:**
- Compaction restoration or any per-turn callback for Antigravity (`PreInvocation` substitute).
- Project-scope Antigravity hooks, repository-local registration, or `pspec doctor` delivery checks for Antigravity.
- Changes to ZuAT beyond bumping the pin.

## Spike results (agy 1.4.10 CLI, Windows, 2026-10-29)

Real `agy -p` sessions against throwaway project-scope hooks. A prototype wrapper (stdin workspace, then the real `pspec resolve hook`, then `injectSteps`) was also run against real consumers.

| Question | Observed |
| --- | --- |
| Hook working directory | The folder containing `hooks.json`: `<project>/.agents` for a project file and `~/.gemini/config` for the global `~/.gemini/config/hooks.json` (run with a temporary file, since deleted) |
| Global file, cwd-only vs payload | Launched in a consumer, `pspec` run from the hook's cwd returned nothing (the predicted silent failure), while the stdin-workspace wrapper delivered the guidance and the model reported it. Same for a path with spaces and parentheses. Launched in a non-consumer directory, both delivered nothing |
| Payload on stdin | `workspacePaths`, `conversationId`, `lastUserInput`, `modelName`, `transcriptPath`, `artifactDirectoryPath`; the host closed stdin immediately (EOF under 1 ms) |
| Workspace environment variable | None. Only `ANTIGRAVITY_CONVERSATION_ID` is set, so stdin stays the only source |
| `systemMessage` / `ephemeralMessage` | Both reached the model. A `systemMessage` also survived `--continue`, while `SessionStart` did not fire again on resume |
| Codex/Claude `hookSpecificOutput` | Not delivered; the `injectSteps` serializer is required |
| Empty output | `{}` and no stdout are both accepted (exit 0). A hook exiting 1 with stderr is non-fatal and delivers nothing |
| Handler format | Flat list works. The grouped `matcher` form under `SessionStart` silently never ran. Unknown keys (`statusMessage`, `additionalContextLimit`) are tolerated |
| Timeout | Enforced: a 2 s timeout on an 8 s hook discarded its output and the session continued |
| Size | 45,000 characters delivered; 70,000 silently dropped |
| Command quoting | `python "C:\path\x.py" arg` silently never ran; the same command unquoted with forward slashes ran. The planned command has neither quotes nor backslashes |
| `PATH` | `pspec` resolves by name under the registry (normal) `PATH` |
| End to end | The wrapper delivered real Powerspec guidance and the model reported it; paths with spaces and parentheses worked; resolution took about 0.4 s |
| Launch from a subdirectory | `workspacePaths` is that subdirectory, not the repository root; nearest-consumer discovery upward still finds the consumer |
| cwd-only failure | `pspec` run from a neutral directory returned nothing, as predicted for a global file |
| Multiple roots (`--add-dir`) | `workspacePaths` is sorted alphabetically (the launch directory has no special place), and every root's `hooks.json` fires once with the same payload |
| Project skills | `.agents`, `.agent`, `_agents`, and `_agent` `skills` all load, including from a subdirectory |

Not tested: the IDE surface, the CLI's global skills directory, and a host that keeps stdin open.

**End to end (2026-10-30, implemented code):** with the dev Powerspec (through a `PATH` shim) and the local Zuat revision, `provision_hooks("antigravity")` wrote the real `~/.gemini/config/hooks.json` (installed, then reused; removed afterwards). Real `agy -p` sessions then reported: a consumer project's token; nothing in a non-consumer directory; and, for a two-root `--add-dir` session, both tokens under their `### <project> (<path>)` headings after the "This session includes several Powerspec projects." instruction. A registry path long enough to exceed Windows `MAX_PATH` inside Zuat's payload store made provisioning report failure after writing the native file; this is the known long-path limit, not Antigravity-specific.

## Decisions

### D1. Payload workspace is an explicit, per-callback capability
`NativeCallback` gains a `payload_workspace` flag, true only for `antigravity/sessionStart`. `pspec resolve hook --stdin-workspace` is validated through `callback_for` and rejected for agents without the flag, before any read. The installed Antigravity command carries the option; direct invocations without it keep today's behavior. This keeps the global "no stdin" rule intact: the exception is opt-in, visible in the installed command, and impossible to enable for Codex or Claude.

Alternatives: always read stdin for Antigravity (hidden magic, direct invocation would hang on a terminal); a generic `--cwd` flag (cannot work, the install is user-level and the project varies per session); register hooks per project in `.agents/hooks.json` so the working directory is `<project>/.agents` and upward discovery works with no stdin (rejected as the primary path: the existing spec forbids falling back to repository-local hooks and it writes into every repository, but it remains the fallback if spike 1.2 shows stdin is unusable).

### D2. Bounded, non-blocking payload read as a portable helper
A domain-neutral helper under `src/powerspec/utils/` reads from a stream on a daemon thread, accumulating bytes and attempting `JSONDecoder.raw_decode` after each chunk. It returns the first complete JSON object, or `None` on timeout (0.5 s, leaving the 1 s metadata inspection budget and the 5 s native limit intact), EOF without an object, or non-object JSON. It never waits for EOF, so a host that keeps the pipe open cannot hang the hook. A terminal stdin (`isatty`) is not read; the caller uses the working directory. Chunked reads use `os.read` on the file descriptor when available and fall back to `read()` for in-memory streams used by test runners.

Portable contract: `read_json_object(stream, timeout) -> dict | None`, with no Powerspec types, no logging, and no exceptions for malformed input. Library fit: the standard library has `json.JSONDecoder.raw_decode` but nothing that returns on the first complete object from an open pipe, so only that decoder is reused. Outside use: any stdin-JSON-protocol hook or helper (for example an editor or Git-hook adapter) that must not wait for EOF. Verification: domain-neutral tests with real pipes for complete-then-open, partial-then-complete, silent, malformed, non-object, oversized-chunked, and terminal inputs; the application caller supplies the budget and interprets `workspacePaths`.

### D3. Workspace selection: every root, the agent picks
The spike showed `workspacePaths` is alphabetical in multi-root sessions, so the launch directory cannot be identified. Multi-root is also the normal shape of an opened Powerspec workset (one linked worktree per repository). The hook therefore resolves every listed path and leaves the choice to the agent, which knows which repository it is implementing or updating changes in.

- One listed path: behave exactly like a single-project session, with no headings.
- Several listed paths: resolve each path's nearest consumer (each path is also the condition cwd for its consumer), count a consumer once, and emit one `systemMessage` that starts with an instruction to follow only the section for the project the agent is actively implementing or updating changes in, then one section per consumer with guidance, headed by the project directory name and path. Labels stay even when only one consumer has guidance, so it is not misapplied to the other projects.
- A failing consumer omits only its own section (stderr names it); the command exits nonzero only when every found consumer fails. The single-consumer rule against returning partial guidance still applies inside each consumer.

Rejected: first entry (arbitrary under alphabetical order); exactly-one-path-or-nothing (delivers nothing in every workset session); merging all consumers' guidance into one unlabeled body (the agent could apply one repository's rules to another).

### D3a. Composition is a portable helper
The per-project sectioning (instruction line, ordered labeled sections, dedupe by key, omission of empty sections) is domain-neutral: `compose_sections(intro, sections) -> str` where sections are `(label, body)` pairs. Library fit: none needed beyond string joining. Outside use: any multi-root hook or report that must label content by origin. Verification: focused tests for ordering, empty-section omission, single-section labeling, and no output when all sections are empty. Powerspec supplies the wording and labels.

### D4. Unusable payload degrades, it does not fail
Empty, timed-out, or non-object payloads, or payloads with no existing workspace directory, write a stderr diagnostic, deliver nothing, and exit zero with empty stdout, with no working-directory fallback. A single missing path among several is skipped with a diagnostic. Falling back would deliver guidance for the wrong repository whenever the fixed host directory happens to be inside one. Configuration and selector errors keep their nonzero exits, as for other agents.

### D5. Envelope and empty output
Guidance is returned as one `systemMessage` step, which persists across turns in the trajectory, matching session-start semantics. `ephemeralMessage` (dropped after the turn) and `userMessage` (impersonates the user) were rejected. The spike showed `systemMessage` also survives `--continue`. No contribution produces empty stdout, as for Codex and Claude; the spike verified Antigravity accepts it, so no agent-specific `{}` exception is needed.

### D6. Registration reuses the neutral provisioning path
`native_document("antigravity")` returns `{"powerspec": {"SessionStart": [handler]}}` with handler `{"type": "command", "command": "pspec resolve hook sessionStart --agent antigravity --stdin-workspace", "timeout": 5}`. `provision_hooks` already writes this to `powerspec.json`, which matches ZuAT's keyed-source rule (stem equals the only top-level key), so inspection, adoption, update, and receipt-repair logic are reused unchanged. The Codex-only `additionalContextLimit` and the `statusMessage` are not emitted.

### D7. Compaction stays unsupported
No `afterCompaction` row exists for `antigravity`, so `callback_for` raises its existing no-verified-mapping error. Logical-selector expansion already derives from `CALLBACKS`, so traits selecting both logical events deliver at session start only. Docs say so; no compensating per-turn hook is added.

### D8. Dependency order
The `zuat` pin in `pyproject.toml` is bumped only to a revision that contains the Zuat change, verified by `uv lock` plus the provisioning tests. Tasks that need the new agent are gated on that bump.

## Risks / Trade-offs

- **Hook contract unverified** (stdin shape, working directory, whether an environment variable already carries the workspace, empty-stdout tolerance, size limits, resume behavior) → spike group 1 before any code. If a documented workspace environment variable exists, replace the stdin read with it and amend the specs first, which would remove D1-D4.
- **Reintroducing stdin reads could re-create the old hang** → bounded thread read, explicit opt-in, and the existing open-stdin subprocess test extended to the new option.
- **The agent may follow the wrong project's section** in a multi-root session → every section is labeled with name and path and the instruction names the selection rule; delivery is not adherence and is reported as such.
- **Multi-root guidance can exceed Antigravity's silent size limit** (45,000 characters delivered, 70,000 dropped in the spike) → sessions are compact by existing requirements; tests assert a realistic four-repository workset stays well under 45,000 characters, and exceeding it is a known limit, not truncated silently by Powerspec.
- **`openspec workset open` for Antigravity is untested** → the multi-root payload shape was verified with `agy --add-dir`; the workset path is checked in the end-to-end task.
- **No compaction restore on Antigravity** → delivered guidance may be lost after compaction; documented limit rather than a heavier per-turn hook.
- **`pspec` may not be on `PATH` for the process Antigravity spawns** → verified in the spike; otherwise document the requirement as for other agents.
- **Guidance size** (Codex has a 5000-character cap) → measure in the spike; the sessionStart body is already compact by existing requirements.
- **Pin bump drags unrelated Zuat changes** → only the verified revision is adopted, and the full suite must pass.

## Migration Plan

Additive. No Antigravity installations exist yet, so there is no legacy registration to migrate; later handler changes use the ordinary outdated-update path. Existing Codex and Claude installs are untouched. Roll back by reverting this change and the pin.

## Open Questions

- Should a later change add a `PreInvocation`-based substitute for compaction restoration if session-start-only delivery proves insufficient?
