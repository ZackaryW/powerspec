from contextlib import contextmanager
import json
from pathlib import Path

from powerspec.sources import SourceBinding
from powerspec.statusing import inspect_status


def put(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def snapshot(root: Path):
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def test_status_reports_effective_bundle_and_source_availability_without_acquisition(tmp_path, monkeypatch):
    import powerspec.workspace as workspace

    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)
    put(project / "openspec/.pspec/config.toml", 'profile="@builtin/main"\nexclude-profiles=[]\n')
    builtin = tmp_path / "builtin"
    put(
        builtin / "profiles/main.toml",
        'contexts=["@builtin/context"]\ntraits=["@builtin/trait"]\n'
        'skills=["@gitsource/tools/skills/*"]\n'
        '[[source]]\nid="tools"\nprovider="git"\norigin="https://example.test/tools"\nreference="main"\n',
    )
    put(builtin / "contexts/context.toml", '[[attach.context]]\nbody="Context"\n')
    put(builtin / "traits/trait.toml", 'hooks=["sessionStart"]\nbody="Trait"\n')
    remote = tmp_path / "remote"
    remote.mkdir()
    calls = []

    class Sources:
        def lookup(self, identity, recipe):
            calls.append(("lookup", identity))
            return SourceBinding(identity, recipe["origin"], recipe["reference"], "a" * 40, "s", "a", remote)

        def ensure(self, *_args, **_kwargs):
            raise AssertionError("status acquired a source")

    @contextmanager
    def resources():
        yield builtin

    monkeypatch.setattr(workspace, "builtin_catalog_root", resources)
    before = snapshot(project)
    result = inspect_status(project, source_store=Sources())
    assert result.profile == "@builtin/main"
    assert result.profiles == ("@builtin/main",)
    assert result.contexts == ("@builtin/context",)
    assert result.traits == ("@builtin/trait",)
    assert result.skills == ("@gitsource/tools/skills/*",)
    assert result.sources[0].status == "available"
    assert calls == [("lookup", "tools")]
    assert snapshot(project) == before


def test_status_cli_emits_one_json_value(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from powerspec.cli import app

    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)
    put(project / "openspec/.pspec/config.toml", 'profile="@builtin/builtin"\nexclude-profiles=["@builtin/zmem-lifecycle","@builtin/adhd-friendly"]\n')
    monkeypatch.chdir(project)
    result = CliRunner().invoke(app, ["status", "--json"])
    assert result.exit_code == 0 and result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["root"] == str(project.resolve())
    assert payload["profile"] == "@builtin/builtin"
