"""Acceptance tests against a real milkpan, with local git repositories through `local:`."""
from pathlib import Path
import subprocess
import tempfile

import pytest

from powerspec.catalog import Catalog
from powerspec.milkpan_client import Milkpan
from powerspec.sources import ExternalCatalogs, MilkpanSources

from milkpan_release_fixture import milkpan_binary


def git(repo: Path, *args):
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def repository(path: Path) -> Path:
    path.mkdir(parents=True)
    git(path, "init", "-b", "main")
    git(path, "config", "user.name", "Powerspec Test")
    git(path, "config", "user.email", "powerspec@example.test")
    return path


@pytest.fixture
def milkpan(tmp_path):
    return Milkpan(milkpan_binary(), tmp_path / "milkpan")


def test_declared_recipe_materializes_and_refreshes(milkpan, tmp_path):
    repo = repository(tmp_path / "src")
    (repo / "resource.txt").write_text("one", encoding="utf-8")
    (repo / ".pspec/profiles").mkdir(parents=True)
    (repo / ".pspec/profiles/base.toml").write_text('scope="user"\n')
    (repo / "openspec/.pspec/profiles").mkdir(parents=True)
    (repo / "openspec/.pspec/profiles/private.toml").write_text('scope="user"\n')
    (repo / "skills/example").mkdir(parents=True)
    (repo / "skills/example/SKILL.md").write_text("---\nname: declared-example\ndescription: Example.\n---\n\nBody\n")
    (repo / "untracked.txt").write_text("not committed", encoding="utf-8")
    git(repo, "add", ".", ":!untracked.txt")
    git(repo, "commit", "-m", "first")
    first_revision = git(repo, "rev-parse", "HEAD")

    source = {"provider": "git", "origin": str(repo), "reference": "main"}
    sources = MilkpanSources(milkpan, consumer_path=tmp_path / "consumer/config.toml")
    observed = sources.ensure("tools", source)
    sources.commit()
    assert observed.resolved_revision == first_revision
    assert (observed.root / "resource.txt").read_text(encoding="utf-8") == "one"
    assert not (observed.root / "untracked.txt").exists() and not (observed.root / ".git").exists()
    assert sources.ensure("tools", source) == observed
    external = ExternalCatalogs().register(observed)
    reusable = Catalog(sources=external.sources())
    assert reusable.get("profile", "@tools/base").name == "base"
    assert ("profile", "@tools/private") not in reusable.resources
    direct = Catalog(gitsources={"tools": observed})
    assert direct.select("skill", "tools/skills/*")[0].name == "declared-example"

    (repo / "resource.txt").write_text("two", encoding="utf-8")
    git(repo, "commit", "-am", "second")
    refreshed = sources.acquire("tools", source)
    sources.commit()
    assert refreshed.resolved_revision == git(repo, "rev-parse", "HEAD")
    assert refreshed.source_id == observed.source_id
    assert (refreshed.root / "resource.txt").read_text(encoding="utf-8") == "two"
    assert sources.lookup("tools", source) == refreshed


def test_two_consumers_share_content_and_update_independently(milkpan, tmp_path):
    repo = repository(tmp_path / "repo")
    (repo / "data").write_text("A")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "A")
    a = MilkpanSources(milkpan, consumer_path=tmp_path / "a/config.toml")
    b = MilkpanSources(milkpan, consumer_path=tmp_path / "b/config.toml")
    recipe = {"provider": "git", "origin": str(repo), "reference": "main"}
    original = a.ensure("tools", recipe)
    a.commit()
    same = b.ensure("tools", recipe)
    b.commit()
    assert same.resolved_revision == original.resolved_revision
    assert same.root == original.root, "one stored commit serves both consumers"

    (repo / "data").write_text("B")
    git(repo, "commit", "-am", "B")
    candidate = a.acquire("tools", recipe)
    assert candidate.resolved_revision != original.resolved_revision
    assert a.lookup("tools", recipe) == original
    a.reject()  # Caller validation rejected a known result.
    assert a.lookup("tools", recipe) == original

    (repo / "data").write_text("C")
    git(repo, "commit", "-am", "C")
    newer = a.acquire("tools", recipe)
    a.commit()
    assert (newer.root / "data").read_text() == "C"
    assert (b.lookup("tools", recipe).root / "data").read_text() == "A"
    milkpan.result("reclaim")
    assert (b.lookup("tools", recipe).root / "data").read_text() == "A", "reclaim keeps selected content"
    assert (a.lookup("tools", recipe).root / "data").read_text() == "C"


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
        remote = repository(root / "remote")
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

        store = MilkpanSources(Milkpan(milkpan_binary(), root / "milkpan"),
                               consumer_path=project / "openspec/.pspec/config.toml")
        source = {"provider": "git", "origin": str(remote), "reference": "main"}
        workspace = importlib.import_module("powerspec.workspace")
        sync = importlib.import_module("powerspec.cli.sync")
        init = importlib.import_module("powerspec.cli.init")
        upgrade = importlib.import_module("powerspec.cli.upgrade")
        monkeypatch.setattr(workspace, "builtin_catalog_root", resources)
        monkeypatch.setattr(sync, "MilkpanSources", lambda **_: store)
        isolated = dict(home=root / "home", registry=root / "registry")
        monkeypatch.setattr(init, "install_consumer", partial(install_consumer, source_store=store, **isolated))
        monkeypatch.setattr(upgrade, "builtin_catalog_root", resources)
        monkeypatch.setattr(upgrade, "MilkpanSources", lambda **_: store)
        monkeypatch.setattr(upgrade, "upgrade_consumer", partial(upgrade_consumer, **isolated))
        with monkeypatch.context() as cwd:
            cwd.chdir(project)
            runner = CliRunner()
            first = runner.invoke(app, ["sync"])
            assert first.exit_code == 1, first.output
            assert "run init" in first.output
            assert "# user comment" in target.read_text()
            assert not store.state_path.exists()
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


def test_plain_milkpan_default_scope_still_works_beside_powerspec(milkpan, tmp_path):
    repo = repository(tmp_path / "repo")
    (repo / "data").write_text("A")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "A")
    sources = MilkpanSources(milkpan, consumer_path=tmp_path / "consumer/config.toml")
    binding = sources.ensure("tools", {"provider": "git", "origin": str(repo), "reference": "main"})
    sources.commit()
    spec = "local:" + str(repo.resolve()).replace("\\", "/")
    plain = milkpan.acquire(f"{spec}@{binding.resolved_revision}", scope="default")
    assert not plain["fetched"], "plain milkpan reuses Powerspec's stored content"
    assert binding.source_id == spec
