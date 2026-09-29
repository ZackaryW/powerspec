def main() -> None:
    """Preserve the original Python entrypoint as a CLI delegate."""
    from powerspec.cli import main as cli_main

    cli_main()
