# Python TDD sections

## scope

Inspect the project's Python version, environment setup, test configuration, and existing tests. Use its established runner and fixture conventions without requiring a switch between pytest, unittest, or another tool.

For a public Python API, assert returned values, documented exceptions, or observable state through that API. For CLI behavior affected by argument parsing or process execution, exercise the actual entrypoint and check exit status, stdout, stderr, and relevant file effects. Keep pure transformations in focused unit tests.

## red

Run the focused test in the intended Python environment. Import failures caused by an incorrect environment are setup failures, not evidence of missing application behavior. Isolate mutable resources using the project's fixture conventions.

## green

Rerun the focused test in the same environment after implementation. If the change affects packaging or entrypoint installation, verify the installed package or command as well as source imports. Report which boundary each check actually exercised.
