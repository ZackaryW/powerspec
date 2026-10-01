# Python TDD resolution review

This records the Markdown returned by the implemented command against a
disposable Codex user installation of the authored skill. Resolution is read
only. It assembles instructions but does not execute the TDD procedure or run
the test command contained in the result.

## Invocation and inputs

Intended invocation: `pspec skill pspec-tdd --agent codex`, from this repository.

- Consumer: `openspec/.pspec/config.toml` selects `@builtin/python-simple-cli`.
- Selected profile: `.pspec/profiles/python-simple-cli.toml` supplies `language = "python"`, `build_tool = "uv"`, `test_runner = "pytest"`, and `test_command = "uv run pytest"`.
- The consumer does not override these inputs, and no current.toml exists for this snapshot.
- The global builtin profile makes bootstrap available; the selected profile makes TDD available. Neither executes a workflow.
- Skill source: `.pspec/skills/pspec_tdd`, copied to the disposable agent's native user skill directory and located through ZuAT.
- Expected outcome: resolved Markdown on stdout by default; `--json` would return status resolved with the same Markdown in content. Expected pending questions: none. The configured language and Python tooling values bypass their prompts.

## Dynamic additions

| Destination `section` | `pos` | `path` | `source_section` |
| --- | --- | --- | --- |
| Scope and expected behavior | `after` | `languages/python.md` | `scope` |
| Red: observe the missing behavior | `after` | `languages/python.md` | `red` |
| Green: implement the increment | `after` | `languages/python.md` | `green` |

The shared body stays in its authored order. Refactor and handoff need no manifest
entries and remain unchanged. The source section headings are included literally;
this example does not invent heading rewriting or recursively process additions.

## Assembled content

The following is the combined text of the actual default Markdown result.
The outer code fence is only for this review document; the command does not emit it.
Relative links retain the installed skill's resource-root meaning.

```markdown
# Test-driven development

Use the project's established test tools for one selected development segment.

When pspec-skill-bootstrap supplies resolved content, follow it in order. [pspec.toml](pspec.toml) declares language-specific additions and where they belong in this shared procedure. Follow bootstrap's handling of pending choices and errors; neither means permission to bypass resolution.

For direct use without bootstrap, consult the manifest's dynamic entries: section names the destination in this document, pos specifies placement, and source_section optionally selects part of the source path. Read the selected content at that placement. Establish the language and any inputs required by the selected additions from configuration or accepted scope; ask only for unresolved choices. Substitute those values into the selected text before following it. Report missing resources rather than silently omitting an addition.

## Scope and expected behavior

Take the requested behavior, accepted constraints, and test environment from the user or calling workflow. This segment does not establish a repository-wide TDD policy or activate a surrounding development process.

Identify the expected outcome, the public boundary where it is observable, and a meaningful example. Resolve material ambiguity from available evidence or the user's decision, preserving choices already settled.

During planning, describe the behavior, expected failure, and verification approach. Planning alone does not authorize implementation. For changes without behavioral effects, such as environment-only maintenance, use appropriate validation and return to the caller without manufacturing a TDD cycle.

Preserve existing implementation and user-authored work. Keep the segment within its authorized scope. When delegated only utility implementation, leave application wiring and integration work with the caller.

<!-- Source: languages/python.md, section: scope -->
## scope

The configured build/environment tool is `uv` and the test runner is `pytest`. Inspect the project's Python version, environment setup, test configuration, and existing tests. Reconcile discrepancies with the configured choices before running tests; configured values do not prove that tools are installed. Preserve established fixture conventions.

For a public Python API, assert returned values, documented exceptions, or observable state through that API. For CLI behavior affected by argument parsing or process execution, exercise the actual entrypoint and check exit status, stdout, stderr, and relevant file effects. Keep pure transformations in focused unit tests.

## Red: observe the missing behavior

Write a focused test expressing the intended outcome and run it before changing production behavior. Confirm it fails because the required behavior is missing. Syntax errors, missing dependencies, and broken test setup do not establish the intended red result.

If the test already passes, determine whether the behavior exists or the test fails to distinguish the change. Do not break working code to manufacture red. For a regression, reproduce the defect with a failing test when possible.

When joining work in progress, preserve existing implementation and distinguish tests added afterward from an observed test-first cycle. Begin TDD with the next appropriate behavior increment rather than deleting work to recreate an earlier stage.

<!-- Source: languages/python.md, section: red -->
## red

Run the focused test using `uv run pytest` with the appropriate test selector in the intended Python environment. Import failures caused by an incorrect environment are setup failures, not evidence of missing application behavior. Isolate mutable resources using the project's fixture conventions.

## Green: implement the increment

Implement enough behavior to satisfy the failing test within the accepted scope. The test establishes evidence for this increment; it does not replace other accepted requirements.

Run the focused test and checks directly affected by the change. Broaden verification when dependencies, failures, or unresolved concerns warrant it. Do not run the full suite after every small increment solely because another TDD cycle occurred; still complete checks required by the project or calling workflow.

Observe actual outcomes at the affected public boundary. For persistent effects, use isolated fixtures and verify the resulting state. Internal mock-call counts alone do not establish externally observable behavior.

<!-- Source: languages/python.md, section: green -->
## green

Rerun the focused test in the same environment after implementation. If the change affects packaging or entrypoint installation, verify the installed package or command as well as source imports. Report which boundary each check actually exercised.

## Refactor and repeat

Once relevant checks pass, improve naming, structure, and duplication where useful without expanding the behavior contract. Rerun affected checks after changes; investigate failures before proceeding.

Return to red for the next accepted behavior increment. Finish the cycle when the requested segment is complete. If progress depends on an unavailable environment or an unresolved decision, report that condition instead of claiming completion.

## Return evidence to the caller

Report the implemented behavior, checks actually run, observed results, and unresolved work. Distinguish an observed red-to-green cycle from tests added after implementation. Separate implementation failures from environment limitations; do not infer execution from test files or claim verification on an unavailable platform.

For a utility-only segment, identify the utility behavior verified and leave application wiring and integration verification explicitly pending. Passing utility tests does not establish completion of the entire feature. Reuse earlier evidence only while it still covers the current implementation and conditions.

Return the evidence and remaining work to the user or caller. Completing this segment does not initiate another development or release step.
```

## Reviewed outcomes

The shared entrypoint still contains bootstrap and direct-use instructions; they
are preserved because the current design retains the shared body. In resolved
use, its conditional direct-use paragraph does not require a second lookup.

The resolved result explicitly consumes the profile's `build_tool = "uv"`,
`test_runner = "pytest"`, and `test_command = "uv run pytest"` in its Python
additions. These inputs are guarded by `language = "python"`; other language
branches do not request them. The rendered command is available even when the
agent has not read OpenSpec context. Values are substituted as text; resolution
does not execute the command or verify that tooling is installed.

The same executable fixture covers the structured resolved response, whose
`content` equals the Markdown above. Separate command fixtures cover an
installed skill without a manifest (`null`), a pending choice, an answer scoped
to one change without leaking into another, and a malformed manifest error.
Environment-only work does not call this command merely because TDD is
installed; skill invocation remains an explicit agent decision or workflow
instruction.
