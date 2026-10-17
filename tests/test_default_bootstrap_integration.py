"""Opt-in real manager/SDK tests through default provisioning, without a client injection."""
from contextlib import contextmanager
from functools import partial
import importlib
import json
import os
from pathlib import Path
import shutil
import tempfile

import pytest
from typer.testing import CliRunner
from zuu.case16 import GitHubReleaseResolver

from powerspec.cli import app
from powerspec.installation import install_consumer
from powerspec.upgrading import upgrade_consumer
from powerspec.sources import SaucepanSources
from test_sources_integration import git


BINARY = os.environ.get('SAUCEPAN_TEST_BINARY')
pytestmark = pytest.mark.skipif(not BINARY, reason='set SAUCEPAN_TEST_BINARY for native bootstrap acceptance')


@pytest.mark.parametrize('recovery', [False, True])
def test_default_bootstrap_acquisition_repeat_and_upgrade(monkeypatch, recovery):
    with tempfile.TemporaryDirectory(prefix='ps-init-') as temporary, monkeypatch.context() as patch:
        root = Path(temporary)
        home = root / 'home'
        home.mkdir()
        patch.setenv('HOME', str(home))
        patch.setenv('USERPROFILE', str(home))
        patch.delenv('POWERSPEC_SAUCEPAN', raising=False)
        patch.delenv('SAUCEPAN_ROOT', raising=False)
        patch.delenv('POWERSPEC_SAUCEPAN_CREDENTIAL_FILE', raising=False)
        patch.setattr(Path, 'home', classmethod(lambda cls: home))
        patch.setenv('CODEX_HOME', str(home / '.codex'))
        target = home / '.saucepan/bin' / ('saucepan.exe' if os.name == 'nt' else 'saucepan')
        if recovery:
            target.parent.mkdir(parents=True)
            shutil.copy2(BINARY, target)
        from powerspec.saucepan_tool import _probe
        version = _probe(Path(BINARY))
        discovery = []
        patch.setattr(GitHubReleaseResolver, 'resolve_version', lambda self: discovery.append(1) or version)
        patch.setattr(GitHubReleaseResolver, 'resolve', lambda self, version, destination, **kwargs: shutil.copy2(BINARY, destination))
        remote = root / 'remote'
        remote.mkdir()
        git(remote, 'init', '-b', 'main')
        git(remote, 'config', 'user.name', 'Test')
        git(remote, 'config', 'user.email', 'test@example.invalid')
        skill = remote / 'skills/example/SKILL.md'
        skill.parent.mkdir(parents=True)
        skill.write_text('---\nname: example\ndescription: Example.\n---\n\nVersion one\n')
        git(remote, 'add', '.')
        git(remote, 'commit', '-m', 'one')
        project = root / 'project'
        project.mkdir()
        git(project, 'init', '-b', 'main')
        config = project / 'openspec/.pspec/config.toml'
        config.parent.mkdir(parents=True)
        config.write_text('[vars]\n')
        (project / 'openspec/config.yaml').write_text('schema: spec-driven\n')
        builtin = root / 'builtin'
        (builtin / 'profiles').mkdir(parents=True)
        (builtin / 'profiles/global.toml').write_text(
            'global=true\nscope="user"\nskills=["tools/skills/*"]\n'
            '[[source]]\nid="tools"\nprovider="git"\n'
            f'origin={json.dumps(str(remote))}\nreference="main"\n')
        @contextmanager
        def resources():
            yield builtin
        patch.setattr('powerspec.workspace.builtin_catalog_root', resources)
        init = importlib.import_module('powerspec.cli.init')
        upgrade = importlib.import_module('powerspec.cli.upgrade')
        patch.setattr(init, 'install_consumer', partial(install_consumer, home=home, registry=root / 'registry'))
        patch.setattr(upgrade, 'builtin_catalog_root', resources)
        patch.setattr(upgrade, 'upgrade_consumer', partial(upgrade_consumer, home=home, registry=root / 'registry'))
        patch.chdir(project)
        runner = CliRunner()
        for expected in ('installed', 'reused'):
            result = runner.invoke(app, ['init', '--agent', 'codex'])
            assert result.exit_code == 0, result.output
            assert expected in result.stdout
        assert (home / '.saucepan/root.json').is_file()
        installed = home / '.codex/skills/example/SKILL.md'
        assert 'Version one' in installed.read_text()
        source = {'provider': 'git', 'origin': str(remote), 'reference': 'main'}
        first = SaucepanSources(consumer_path=config).lookup('tools', source)
        skill.write_text(skill.read_text().replace('Version one', 'Version two'))
        git(remote, 'commit', '-am', 'two')
        result = runner.invoke(app, ['upgrade', '--agent', 'codex'])
        assert result.exit_code == 0, result.output
        assert 'Version two' in installed.read_text()
        latest = SaucepanSources(consumer_path=config).lookup('tools', source)
        assert latest.resolved_revision != first.resolved_revision
        assert latest.resolved_revision == git(remote, 'rev-parse', 'HEAD')
        assert discovery == [1]
        assert len(list(home.glob('.powerspec-saucepan-backup-*'))) == int(recovery)
