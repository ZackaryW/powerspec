"""Opt-in acceptance test against the real pinned Saucepan CLI/SDK."""
import os
from pathlib import Path
import subprocess
import tempfile

import pytest
from saucepan_sdk import Client

from powerspec.catalog import Catalog
from powerspec.sources import ExternalCatalogs, SaucepanSources


BINARY = os.environ.get("SAUCEPAN_TEST_BINARY")
pytestmark = pytest.mark.skipif(not BINARY, reason="set SAUCEPAN_TEST_BINARY for real Saucepan acceptance")


def git(repo: Path, *args):
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def test_powerspec_app_materializes_and_refreshes_declared_recipe():
    # Saucepan documents short test roots as required on Windows.
    with tempfile.TemporaryDirectory(prefix="ps-sp-") as temporary:
        root = Path(temporary)
        repo = root / "src"
        repo.mkdir()
        git(repo, "init", "-b", "main")
        git(repo, "config", "user.name", "Powerspec Test")
        git(repo, "config", "user.email", "powerspec@example.test")
        (repo / "resource.txt").write_text("one", encoding="utf-8")
        (repo / ".pspec/profiles").mkdir(parents=True)
        (repo / ".pspec/profiles/base.toml").write_text('scope="user"\n')
        (repo / "openspec/.pspec/profiles").mkdir(parents=True)
        (repo / "openspec/.pspec/profiles/private.toml").write_text('scope="user"\n')
        (repo / "skills/example").mkdir(parents=True)
        (repo / "skills/example/SKILL.md").write_text(
            "---\nname: declared-example\ndescription: Example.\n---\n\nBody\n"
        )
        git(repo, "add", ".")
        git(repo, "commit", "-m", "first")
        first_revision = git(repo, "rev-parse", "HEAD")

        base = Client(executable=BINARY, root=str(root / "store"))
        source = {"provider": "git", "origin": str(repo), "reference": "main"}
        sources = SaucepanSources(base, consumer_path=root / "consumer/config.toml")
        observed = sources.ensure("tools", source)
        sources.commit()
        assert observed.resolved_revision == first_revision
        assert (observed.root / "resource.txt").read_text(encoding="utf-8") == "one"
        assert sources.ensure("tools", source) == observed
        external = ExternalCatalogs().register(observed)
        reusable = Catalog(sources=external.sources())
        assert reusable.get("profile", "@tools/base").name == "base"
        assert ("profile", "@tools/private") not in reusable.resources
        direct = Catalog(gitsources={"tools": observed})
        assert direct.select("skill", "tools/skills/*")[0].name == "declared-example"

        (repo / "resource.txt").write_text("two", encoding="utf-8")
        git(repo, "commit", "-am", "second")
        second_revision = git(repo, "rev-parse", "HEAD")
        refreshed = sources.acquire("tools", source)
        sources.commit()
        assert refreshed.resolved_revision == second_revision
        assert refreshed.source_id == observed.source_id
        assert (refreshed.root / "resource.txt").read_text(encoding="utf-8") == "two"


def test_fresh_sync_init_and_upgrade_lifecycle(monkeypatch):
    from contextlib import contextmanager
    from functools import partial
    import importlib
    import json
    from typer.testing import CliRunner
    from powerspec.cli import app
    from powerspec.installation import install_consumer
    from powerspec.upgrading import upgrade_consumer
    from test_installation import put

    with tempfile.TemporaryDirectory(prefix="ps-life-") as temporary:
        root = Path(temporary)
        remote = root / "remote"
        remote.mkdir()
        git(remote, "init", "-b", "main")
        git(remote, "config", "user.name", "Test")
        git(remote, "config", "user.email", "test@example.invalid")
        skill = remote / "skills/example/SKILL.md"
        put(skill, "---\nname: example\ndescription: Example.\n---\n\nVersion one\n")
        git(remote, "add", ".")
        git(remote, "commit", "-m", "first")
        original_revision = git(remote, "rev-parse", "HEAD")
        project = root / "project"
        project.mkdir()
        git(project, "init", "-b", "main")
        put(project / "openspec/.pspec/config.toml", "[vars]\n")
        target = project / "openspec/config.yaml"
        put(target, "schema: spec-driven\n# user comment\n")
        builtin = root / "builtin"
        put(builtin / "profiles/global.toml",
            'global=true\nscope="user"\nskills=["tools/skills/*"]\n'
            'contexts=["@builtin/base"]\n[[source]]\nid="tools"\nprovider="git"\n'
            f'origin={json.dumps(str(remote))}\nreference="main"\n')
        put(builtin / "contexts/base.toml", '[[attach.context]]\nbody="Lifecycle guidance"\n')

        @contextmanager
        def resources():
            yield builtin

        store = SaucepanSources(Client(executable=BINARY, root=str(root / "store")), consumer_path=project / "openspec/.pspec/config.toml")
        source = {"provider": "git", "origin": str(remote), "reference": "main"}
        workspace = importlib.import_module("powerspec.workspace")
        sync = importlib.import_module("powerspec.cli.sync")
        init = importlib.import_module("powerspec.cli.init")
        upgrade = importlib.import_module("powerspec.cli.upgrade")
        monkeypatch.setattr(workspace, "builtin_catalog_root", resources)
        monkeypatch.setattr(sync, "SaucepanSources", lambda **_: store)
        isolated = dict(home=root / "home", registry=root / "registry")
        monkeypatch.setattr(init, "install_consumer", partial(install_consumer, source_store=store, **isolated))
        monkeypatch.setattr(upgrade, "builtin_catalog_root", resources)
        monkeypatch.setattr(upgrade, "SaucepanSources", lambda **_: store)
        monkeypatch.setattr(upgrade, "upgrade_consumer", partial(upgrade_consumer, **isolated))
        # This also keeps Windows from retaining the temporary working directory
        # when TemporaryDirectory removes it after the test.
        with monkeypatch.context() as cwd:
            cwd.chdir(project)
            runner = CliRunner()
            first = runner.invoke(app, ["sync"])
            assert first.exit_code == 1, first.output
            assert "run init" in first.output
            assert "# user comment" in target.read_text()
            assert not store.state_path.exists()
            assert not (root / "home").exists()
            for status in ("installed", "reused"):
                result = runner.invoke(app, ["init", "--agent", "codex"])
                assert result.exit_code == 0, result.output
                assert status in result.stdout
            installed = root / "home/.codex/skills/example/SKILL.md"
            assert "Version one" in installed.read_text()
            assert runner.invoke(app, ["sync"]).exit_code == 0
            before = target.read_bytes()
            skill.write_text(skill.read_text().replace("Version one", "Version two"))
            git(remote, "commit", "-am", "second")
            repeated = runner.invoke(app, ["sync"])
            assert repeated.exit_code == 0, repeated.output
            assert target.read_bytes() == before
            assert store.lookup("tools", source).resolved_revision == original_revision
            assert "Version one" in installed.read_text()
            refreshed = runner.invoke(app, ["upgrade", "--agent", "codex"])
            assert refreshed.exit_code == 0, refreshed.output
            assert store.lookup("tools", source).resolved_revision == git(remote, "rev-parse", "HEAD")
            assert "Version two" in installed.read_text()


def test_two_consumers_lost_receipt_and_rejected_candidate():
    from saucepan_sdk import TransportError
    from saucepan_sdk.transport import CliTransport
    from powerspec.catalog import ConfigurationError
    with tempfile.TemporaryDirectory(prefix='ps-pins-') as temporary:
        root = Path(temporary)
        repo = root / 'repo'
        repo.mkdir()
        git(repo, 'init', '-b', 'main')
        git(repo, 'config', 'user.name', 'Test')
        git(repo, 'config', 'user.email', 'test@example.invalid')
        (repo / 'data').write_text('A')
        git(repo, 'add', '.')
        git(repo, 'commit', '-m', 'A')
        class LostReceipt(CliTransport):
            lose = True
            def json(self, config, call):
                result = super().json(config, call)
                if call.argv[0] == 'prepare-group' and self.lose:
                    self.lose = False
                    raise TransportError('timeout', started=True, indeterminate=True)
                return result
        transport = LostReceipt()
        client = Client(executable=BINARY, root=str(root / 'store'), transport=transport)
        a = SaucepanSources(client, consumer_path=root / 'a/config.toml')
        b = SaucepanSources(client, consumer_path=root / 'b/config.toml')
        recipe = {'provider': 'git', 'origin': str(repo), 'reference': 'main'}
        with pytest.raises(ConfigurationError, match='may have committed'):
            a.ensure('tools', recipe)
        pending = a._state()['pending'].copy()
        original = a.ensure('tools', recipe)
        assert a._state()['pending'] == pending
        a.commit()
        same = b.ensure('tools', recipe)
        b.commit()
        assert same.resolved_revision == original.resolved_revision
        (repo / 'data').write_text('B')
        git(repo, 'commit', '-am', 'B')
        candidate = a.acquire('tools', recipe)
        assert candidate.resolved_revision != original.resolved_revision
        assert a.lookup('tools', recipe) == original
        a.reject()  # Caller validation rejected a known, successfully pinned result.
        (repo / 'data').write_text('C')
        git(repo, 'commit', '-am', 'C')
        newer = a.acquire('tools', recipe)
        a.commit()
        assert (newer.root / 'data').read_text() == 'C'
        assert (b.lookup('tools', recipe).root / 'data').read_text() == 'A'
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as pool:
            reclaim = pool.submit(client.reclaim)
            assert (b.lookup('tools', recipe).root / 'data').read_text() == 'A'
            reclaim.result()
        assert (original.root / 'data').read_text() == 'A'
        assert (candidate.root / 'data').read_text() == 'B'
