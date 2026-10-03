# Runtime trait hook delivery

`pspec init --agent codex` and `pspec init --agent claude` install one generic
user-level hook asset through ZuAT. The asset contains commands only. It does not
contain a consumer profile, trait body, or repository path. At invocation, the
host sends JSON on stdin and Powerspec uses its absolute `cwd` to discover the
nearest `openspec/.pspec/config.toml` within the current Git or worktree boundary.

The verified mappings are:

| Powerspec event | Agent | Native callback | Native matcher |
| --- | --- | --- | --- |
| `sessionStart` | Codex | `SessionStart` | `startup|resume|clear` |
| `afterCompaction` | Codex | `SessionStart` | `compact` |
| `sessionStart` | Claude | `SessionStart` | `startup|resume|clear|fork` |
| `afterCompaction` | Claude | `SessionStart` | `compact` |

Both hosts document that `SessionStart` can inject `hookSpecificOutput.additionalContext`
and fires again with `source = "compact"`. Their native `PostCompact` callbacks can
run commands, but do not provide context delivery, so Powerspec does not claim or
install a `PostCompact` mapping. Kimi and Pi remain unsupported for these two
logical delivery events until a native callback, input contract, and context
response are verified. Initialization reports that unsupported state without
inventing an event spelling.

These contracts are defined by the current [Codex hooks documentation](https://developers.openai.com/de-DE/docs/hooks)
and [Claude Code hooks reference](https://code.claude.com/docs/en/hooks). ZuAT owns
the native settings merge, ownership record, conflict checks, and repeated-install
reuse. Powerspec owns logical event selection and response serialization.

The native startup path was exercised on 2026-10-02 with Codex CLI 0.159.1 and
Claude Code 2.1.265 using disposable settings. Both hosts supplied the documented
`SessionStart` JSON including absolute `cwd`, and both accepted the returned
`additionalContext`. The Codex walkthrough repeated `pspec-skill-bootstrap` from
the delivered guidance. The Claude walkthrough exposed the guidance to the model,
which independently declined to follow skill names absent from that disposable
host's installed-skill inventory. That is a successful delivery check and a
separate adherence failure, not evidence that the skill ran. Automated adapter
tests cover the same native response with `source = "compact"`, plus ordinary
skill `null`, pending, answered, and malformed-manifest outcomes.

## Trait selectors

A runtime trait selects one or more logical events:

```toml
hooks = ["sessionStart", "afterCompaction"]
body = "Read and follow <skill:pspec-skill-bootstrap> before resolving another skill."
```

An agent-qualified selector such as `codex:SessionStart` selects every supported
Powerspec mapping carried by that native callback. Prefix a selector with `~` to
remove it from that trait after all positive selectors have expanded:

```toml
hooks = ["sessionStart", "afterCompaction", "~claude:SessionStart"]
```

The exclusion affects only that trait. It does not remove the shared native
registration, another trait, or the other agent's callback. Unsupported logical
or qualified native selectors are configuration errors. `PostCompact` is not a
supported context-delivery selector.

## Dispatch

Native registrations call one of these commands and pass the native payload on
stdin:

```console
pspec resolve hook sessionStart --agent codex
pspec resolve hook afterCompaction --agent codex
```

`pspec` and `powerspec` expose the same command. The dispatcher validates the
native event, source, and absolute event `cwd`; discovers the consumer; composes
the current effective bundle after profile exclusions; selects only matching
traits; and evaluates their optional `when` expressions from a fresh runtime
snapshot. An explicit `--change NAME` enables that change's scoped values.
Powerspec never infers a change from ambient state.

No consumer, no matching trait, or all false conditions produces no stdout.
Successful guidance is returned using the host's native JSON context shape. A
malformed nearest consumer, invalid selector, failed probe, non-Boolean condition,
or invalid payload writes a diagnostic to stderr and exits nonzero without a
partial guidance object. Dispatch does not publish contexts, install assets,
prompt for skill variables, execute skills, or write consumer state.

Conditions are trusted Python rules evaluated through Zuu case18. They can read
`vars`, call `armed(kind, ref)`, use `which(name)`, inspect `git_root`, and invoke
`run_json(argv)`. `armed` means selected in the effective bundle after exclusions;
it does not mean installed, event-matched, or condition-true. `run_json` uses the
event cwd and environment, requires an exit-zero JSON object, and has a five-second
subprocess timeout. These capabilities are not a sandbox and their external
effects are not rolled back.

## Installation and recovery

Hook installation always targets the selected agent's user scope, even when a
selected profile installs its skills at project scope. Repeating `pspec init`
reuses an unchanged owned registration. ZuAT preserves unrelated settings and
reports unmanaged or edited conflicts without overwriting them. Correct the
reported native settings or ownership conflict and rerun `pspec init`.

Codex requires review of new or changed non-managed hooks before it executes
them. Open `/hooks`, inspect the Powerspec commands, and trust the current
definition. This host trust decision is separate from ZuAT's ownership record.

Installation proves only that the registration is present. A successful hook
process proves only invocation. Native additional-context delivery, the agent's
subsequent adherence, and execution of a referenced skill are separate outcomes.
The builtin bootstrap trait supplies a bounded reminder; it does not activate
TDD, BDD, or any other workflow by itself.
