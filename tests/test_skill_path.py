import json
from pathlib import Path

import pytest

from test_skill_cli import environment, installed, invoke, put, snapshot


@pytest.mark.parametrize('form', ['', 'SKILL.md', 'pspec.toml'])
def test_native_selected_path_needs_no_installed_adapter(tmp_path, monkeypatch, form):
    import zuat.pub
    home, project = environment(tmp_path, monkeypatch)
    installed(home, default='wrong')
    selected = project / 'plugin skills' / 'chosen'
    put(selected / 'SKILL.md', '---\nname: example\n---\n\nUse <language>.\n')
    put(selected / 'pspec.toml', 'version=2\nentry="SKILL.md"\n[[input]]\nid="language"\ntype="string"\ndefault="selected"\n')
    monkeypatch.setattr(zuat.pub, 'locate_skill', lambda *a, **k: pytest.fail('native lookup'))
    before = snapshot(tmp_path)
    result = invoke(['resolve', 'skill', '--path', str((selected / form).relative_to(project)), '--agent', 'native-plugin', '--json'])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload['skill'] == 'example' and payload['skill_path'] == str(selected.resolve())
    assert 'selected' in payload['content'] and 'wrong' not in payload['content']
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize('extra', [[], ['--selected', 'ignored'], ['--path', 'ignored']])
def test_legacy_names_are_migration_errors(extra):
    result = invoke(['resolve', 'skill', 'example', '--agent', 'codex', *extra])
    assert result.exit_code != 0 and result.stdout == ''
    assert '--path' in result.stderr and 'native' in result.stderr.lower()


def test_invalid_paths_never_fall_back_to_installed_copy(tmp_path, monkeypatch):
    home, project = environment(tmp_path, monkeypatch)
    installed(home, default='wrong')
    unrelated = put(project / 'example.txt', 'unrelated')
    for path in (unrelated, project / 'missing', project):
        result = invoke(['resolve', 'skill', '--path', str(path), '--agent', 'codex'])
        assert result.exit_code != 0 and result.stdout == ''


def test_pending_path_and_change_are_reused(tmp_path, monkeypatch):
    import shlex
    home, project = environment(tmp_path, monkeypatch)
    selected = installed(home, name='with-space', manifest='version=2\nentry="SKILL.md"\n[[input]]\nid="language"\ntype="string"\n[input.parser]\ntype="prompt"\nprompt="Language?"\n')
    (project / '.git').mkdir()
    put(project / 'openspec/.pspec/config.toml', 'exclude-profiles=["@builtin/zmem-lifecycle", "@builtin/adhd-friendly"]\n')
    args = ['resolve', 'skill', '--path', str(selected), '--agent', 'codex', '--change', 'one']
    pending = invoke(args)
    assert pending.exit_code == 0, pending.output
    command = pending.stdout.strip().splitlines()[-1].strip('`')
    argv = shlex.split(command, posix=False)
    argv = [part[1:-1] if part.startswith('"') and part.endswith('"') else part for part in argv]
    assert argv[argv.index('--path') + 1] == str(selected.resolve())
    put(project / 'openspec/.pspec/current.toml', '[_change.one]\nlanguage="python"\n')
    resolved = invoke(argv[1:])
    assert resolved.exit_code == 0 and 'Use python.' in resolved.stdout


@pytest.mark.parametrize('target', ['outside', 'missing'])
def test_manifest_symlinks_cannot_escape_or_mask_broken_entries(tmp_path, monkeypatch, target):
    home, project = environment(tmp_path, monkeypatch)
    selected = installed(home, default='python')
    manifest = selected / 'pspec.toml'
    manifest.unlink()
    outside = project / target
    if target == 'outside':
        put(outside, 'version=2\nentry="SKILL.md"')
    try:
        manifest.symlink_to(outside)
    except OSError as error:
        pytest.skip(f'symlinks unavailable: {error}')
    result = invoke(['resolve', 'skill', '--path', str(selected), '--agent', 'codex'])
    assert result.exit_code == 1 and result.stdout == ''
    assert 'pspec.toml' in result.stderr
