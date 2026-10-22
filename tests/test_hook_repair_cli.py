from contextlib import nullcontext
from importlib import import_module
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from powerspec.cli import app
from powerspec.provisioning import HookOutcome
from powerspec.upgrading import UpgradeResult


@pytest.mark.parametrize(("options", "force", "repair"), [
    ([], False, False), (["--force"], True, False),
    (["--repair-hooks"], False, True), (["--force", "--repair-hooks"], True, True),
])
@pytest.mark.parametrize("success", [True, False])
def test_upgrade_hook_authorization_output_and_exit(tmp_path, monkeypatch, options, force, repair, success):
    cli = import_module("powerspec.cli.upgrade")
    consumer = SimpleNamespace(config_path=tmp_path / "openspec/.pspec/config.toml")
    monkeypatch.setattr(cli, "discover_consumer", lambda *a, **kw: consumer)
    monkeypatch.setattr(cli, "builtin_catalog_root", lambda: nullcontext(tmp_path))
    monkeypatch.setattr(cli, "SaucepanSources", lambda **kw: object())
    seen = []
    def upgrade(**kwargs):
        seen.append((kwargs["force"], kwargs["repair_hooks"]))
        return UpgradeResult(
            "success" if success else "failed",
            hooks=HookOutcome("codex", "updated" if success else "failed",
                              () if success else ("provider repair failed",), "op-recovery"),
        )
    monkeypatch.setattr(cli, "upgrade_consumer", upgrade)
    result = CliRunner().invoke(app, ["upgrade", "--agent", "codex", *options])
    assert result.exit_code == (0 if success else 1), result.output
    assert seen == [(force, repair)]
    assert "op-recovery" in (result.stdout if success else result.stderr)
    assert ("Upgrade complete." in result.stdout) is success
    if not success:
        assert "provider repair failed" in result.stderr


def test_upgrade_help_distinguishes_skill_force_from_receipt_repair():
    result = CliRunner().invoke(app, ["upgrade", "--help"], color=False)
    assert result.exit_code == 0
    assert "--repair-hooks" in result.stdout
    assert "--force" in result.stdout and "skills" in result.stdout
