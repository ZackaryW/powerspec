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
from saucepan_release_fixture import released_provider
from saucepan_sdk import Client
import subprocess
import hashlib
from uuid import uuid4

from powerspec.cli import app
from powerspec.installation import install_consumer
from powerspec.upgrading import upgrade_consumer
from powerspec.sources import SaucepanSources
from test_sources_integration import git


ASSETS = os.environ.get('SAUCEPAN_RELEASE_ASSETS')
BINARY = os.environ.get('SAUCEPAN_TEST_BINARY')
pytestmark = pytest.mark.skipif(not ASSETS or not BINARY, reason='set SAUCEPAN_RELEASE_ASSETS and SAUCEPAN_TEST_BINARY for native bootstrap acceptance')


@pytest.mark.parametrize('recovery', [False, True])
def test_default_bootstrap_acquisition_repeat_and_upgrade(monkeypatch, recovery):
    with released_provider(ASSETS) as (provider, requests):
        _bootstrap_acquisition(monkeypatch, recovery, provider, requests)


def _bootstrap_acquisition(monkeypatch, recovery, provider, requests):
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
        from powerspec import saucepan_bootstrap as bootstrap
        patch.setattr(bootstrap, 'ensure_default', partial(bootstrap.ensure_default, provider=provider))
        if recovery:
            Client(executable=BINARY, root=str(target.parent.parent)).init()
            shutil.copy2(BINARY, target)
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            operation = str(uuid4())
            args = [str(Path(ASSETS) / 'install.ps1'), '-Version', provider.tag, '-Root', str(target.parent.parent),
                    '-Operation', operation, '-MigrateUnmanaged', '-ExpectedSha256', digest,
                    '-TestReleaseBase', provider.release_base, '-TestGithubApi', provider.fixture_api]
            if os.name == 'nt':
                command = ['powershell.exe', '-NoProfile', '-File', *args]
            else:
                command = ['sh', str(Path(ASSETS) / 'install.sh'), '--version', provider.tag,
                    '--root', str(target.parent.parent), '--operation', operation, '--migrate-unmanaged',
                    '--expected-sha256', digest, '--test-release-base', provider.release_base,
                    '--test-github-api', provider.fixture_api]
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=180)
            assert result.returncode == 0, result.stderr
            receipt = json.loads(result.stdout)
            assert receipt['status'] == 'complete'
            assert hashlib.sha256(Path(receipt['backup_paths'][0]).read_bytes()).hexdigest() == digest
        setup_requests = None
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
            if setup_requests is None:
                setup_requests = len(requests)
            else:
                assert len(requests) == setup_requests
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
        assert len(requests) == setup_requests
        assert not list(home.glob('.powerspec-saucepan-backup-*'))
