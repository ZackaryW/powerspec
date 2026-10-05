# Python TDD sections

## scope

The configured build/environment tool is `<build_tool>` and the test runner is `<test_runner>`. Inspect the project's Python version, environment setup, test configuration, and existing tests. Reconcile discrepancies with the configured choices before running tests; configured values do not prove that tools are installed. Preserve established fixture conventions.

For a public Python API, assert returned values, documented exceptions, or observable state through that API. For CLI behavior affected by argument parsing or process execution, exercise the actual entrypoint and check exit status, stdout, stderr, and relevant file effects. Keep pure transformations in focused unit tests.

## red

Run the focused test using `<test_command>` with the appropriate test selector in the intended Python environment. Import failures caused by an incorrect environment are setup failures, not evidence of missing application behavior. Isolate mutable resources using the project's fixture conventions.

## green

Rerun the focused test in the same environment after implementation. If the change affects packaging or entrypoint installation, verify the installed package or command as well as source imports. Report which boundary each check actually exercised.
