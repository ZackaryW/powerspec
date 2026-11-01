"""pspec doctor --force-reset: delete the shared bucket, ~/.powerspec and this project's state."""
import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from powerspec.cli import app


@pytest.fixture
def machine(tmp_path, monkeypatch):
    home = tmp_path / 'home'
    home.mkdir()
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: home))
    monkeypatch.delenv('MILKPAN_HOME', raising=False)
    bucket = home / '.milkpan'
    (bucket / 'blobs/sha256/ab').mkdir(parents=True)
    (bucket / 'blobs/sha256/ab/cd').write_text('content')
    (bucket / 'state.json').write_text('{}')
    (bucket / 'milkpan.toml').write_text('# shared policy\n')
    powerspec = home / '.powerspec'
    powerspec.mkdir()
    (powerspec / 'config.toml').write_text('[vars]\n')
    (powerspec / 'worksets.toml').write_text('')
    project = tmp_path / 'project'
    (project / '.git').mkdir(parents=True)
    state = project / 'openspec/.pspec'
    state.mkdir(parents=True)
    (state / 'config.toml').write_text('[vars]\n')
    (state / 'milkpan-state.json').write_text('{}')
    monkeypatch.chdir(project)
    return home, bucket, powerspec, state


def test_confirmed_reset_removes_everything(machine):
    home, bucket, powerspec, state = machine
    result = CliRunner().invoke(app, ['doctor', '--force-reset', '--yes', '--json'])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload['ok'] and not payload['reset']['remaining']
    assert not bucket.exists() and not powerspec.exists()
    assert not (state / 'milkpan-state.json').exists()
    assert (state / 'config.toml').exists(), 'the project configuration itself stays'


def test_non_interactive_reset_without_yes_deletes_nothing(machine):
    home, bucket, powerspec, state = machine
    result = CliRunner().invoke(app, ['doctor', '--force-reset'])
    assert result.exit_code == 1
    assert 'rerun with --yes' in result.output
    assert bucket.exists() and powerspec.exists() and (state / 'milkpan-state.json').exists()


def test_unrecognized_milkpan_home_is_refused(machine, tmp_path, monkeypatch):
    home, bucket, powerspec, state = machine
    unrelated = tmp_path / 'my-documents'
    unrelated.mkdir()
    (unrelated / 'thesis.docx').write_text('important')
    monkeypatch.setenv('MILKPAN_HOME', str(unrelated))
    result = CliRunner().invoke(app, ['doctor', '--force-reset', '--yes'])
    assert result.exit_code == 1 and 'does not look like a milkpan bucket' in result.output
    assert (unrelated / 'thesis.docx').exists() and powerspec.exists(), 'a refusal deletes nothing'


def test_home_directory_as_bucket_is_refused(machine, monkeypatch):
    home, _, powerspec, _ = machine
    monkeypatch.setenv('MILKPAN_HOME', str(home))
    result = CliRunner().invoke(app, ['doctor', '--force-reset', '--yes'])
    assert result.exit_code == 1 and 'home directory' in result.output
    assert powerspec.exists()


@pytest.mark.skipif(os.name != 'nt', reason='open files block deletion only on Windows')
def test_files_in_use_are_reported_as_remaining(machine):
    home, bucket, powerspec, _ = machine
    held = open(bucket / 'blobs/sha256/ab/cd', 'rb')
    try:
        result = CliRunner().invoke(app, ['doctor', '--force-reset', '--yes', '--json'])
    finally:
        held.close()
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert any('cd' in path for path in payload['reset']['remaining'])
    assert not powerspec.exists(), 'everything else is still removed'
