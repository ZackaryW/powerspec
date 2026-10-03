import os
import sys
import pytest
from powerspec.catalog import Catalog, ConfigurationError
from powerspec.consumer import discover_consumer
from powerspec.profiles import compose
from powerspec.conditions import Invocation, evaluate, context_contributions, trait_contributions
from powerspec.resources import builtin_catalog_root


def put(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


@pytest.fixture
def bundle(tmp_path):
    put(tmp_path, 'profiles/main.toml', 'contexts=["@builtin/example"]\ntraits=["@builtin/a", "@builtin/b"]\nskills=["@builtin/example"]\n[vars]\nlabel="profile"')
    put(tmp_path, 'contexts/example.toml', '[[attach.context]]\nbody="context"\nwhen="vars[\'label\'] == \'config\'"')
    put(tmp_path, 'traits/a.toml', 'hooks=["sessionStart"]\nbody="a"\nwhen="armed(\'trait\', \'@builtin/b\')"')
    put(tmp_path, 'traits/b.toml', 'hooks=["otherEvent"]\nbody="b"\nwhen="armed(\'trait\', \'@builtin/a\') and vars[\'label\'] == \'change\'"')
    put(tmp_path, 'skills/folder/SKILL.md', '---\nname: example\n---\n')
    return compose(Catalog(builtin=tmp_path), '@builtin/main', agent='codex')


def test_capabilities_short_circuit_and_fresh_values(tmp_path, bundle):
    (tmp_path / '.git').write_text('gitdir: worktree')
    calls = []
    def probe(argv, **kwargs):
        calls.append((argv, kwargs))
        return {'ok': False}
    invocation = Invocation(tmp_path, env={'PATH': '', 'EXAMPLE': 'yes'}, probe=probe)
    def run(code, values=None):
        return evaluate(code, values=values or {}, bundle=bundle, invocation=invocation, location='trait:test')
    assert run("which('not-installed') is None or run_json(['unused']).get('ok') is True")
    assert not calls
    assert run("run_json(['probe']).get('ok') is False")
    assert calls == [(['probe'], {'cwd': tmp_path, 'env': {'PATH': '', 'EXAMPLE': 'yes'}, 'timeout': 5})]
    assert run("git_root.name == vars['repo']", {'repo': tmp_path.name})
    assert run("armed('profile', '@builtin/main') and vars['armed'] is False", {'armed': False})
    assert run("vars['answer'] == 1", {'answer': 1})
    assert not run("vars['answer'] == 1", {'answer': 2})


@pytest.mark.parametrize('code', ["1", "[]", "missing()", "len([]) == 0", "vars.__class__ is None",
                                  "run_json('command') is None", "armed('unknown', '@builtin/a')",
                                  "1 / 0", "x = True"])
def test_errors_are_located_not_false(tmp_path, bundle, code):
    with pytest.raises(ConfigurationError, match='example.toml/when'):
        evaluate(code, values={}, bundle=bundle, invocation=Invocation(tmp_path), location='example.toml/when')


def test_missing_git_context_only_fails_when_used(tmp_path, bundle, monkeypatch):
    import powerspec.conditions as conditions
    monkeypatch.setattr(conditions, 'find_git_root', lambda cwd: None)
    invocation = Invocation(tmp_path)
    assert evaluate('True or git_root.is_dir()', values={}, bundle=bundle, invocation=invocation, location='test')
    with pytest.raises(ConfigurationError, match='git_root'):
        evaluate('git_root.is_dir()', values={}, bundle=bundle, invocation=invocation, location='test')


def test_compiletime_runtime_timing_and_selection(tmp_path, bundle):
    (tmp_path / '.git').mkdir()
    put(tmp_path, 'openspec/.pspec/config.toml', '[vars]\nlabel="config"')
    put(tmp_path, 'openspec/.pspec/current.toml', '[vars]\nlabel="current"\n[_change.one]\nlabel="change"')
    consumer = discover_consumer(tmp_path)
    invocation = Invocation(tmp_path)
    assert [c.body for c in context_contributions(bundle, consumer, invocation)] == ['context']
    refs = [r.ref for r in bundle.traits]
    assert [c.body for c in trait_contributions(bundle, consumer, invocation, matching_refs=refs)] == ['a']
    assert [c.body for c in trait_contributions(bundle, consumer, invocation, matching_refs=refs, change='one')] == ['a', 'b']
    assert [c.body for c in trait_contributions(bundle, consumer, invocation, matching_refs=refs[:1], change='one')] == ['a']
    for kind, ref in [('profile', '@builtin/main'), ('context', '@builtin/example'), ('skill', '@builtin/example'), ('trait', '@builtin/b')]:
        assert bundle.armed(kind, ref)
    assert not bundle.armed('skill', '@builtin/absent')
    assert not bundle.armed('trait', '@builtin/example')
    assert not bundle.armed('skill', 'missing/skills/unavailable')
    assert not bundle.armed('skill', 'missing/skills/*')


def test_batch_has_no_successful_partial_output(tmp_path, bundle):
    bundle.traits[1].data['when'] = 'missing_callback()'
    invocation = Invocation(tmp_path)
    # Caller-owned event matching prevents execution of unrelated callbacks.
    assert len(trait_contributions(bundle, None, invocation, matching_refs=['@builtin/a'])) == 1
    result = None
    with pytest.raises(ConfigurationError, match='b.toml'):
        result = trait_contributions(bundle, None, invocation, matching_refs=['@builtin/a', '@builtin/b'])
    assert result is None
    bundle.contexts[0].data['attach']['context'][0]['when'] = 'True'
    bundle.contexts[0].data['attach']['context'].append({'body': 'bad', 'when': 'missing_callback()'})
    with pytest.raises(ConfigurationError, match='example.toml'):
        context_contributions(bundle, None, invocation)


def test_real_probe_object_and_process_errors(tmp_path, bundle):
    invocation = Invocation(tmp_path, env=dict(os.environ, PSPEC_PROBE='ok'))
    code = 'import os,json; print(json.dumps({"ok": False,"cwd":os.getcwd(),"env":os.environ["PSPEC_PROBE"]}))'
    expr = f"run_json({[sys.executable, '-c', code]!r})"
    assert evaluate(expr+"['env'] == 'ok'", values={}, bundle=bundle, invocation=invocation, location='probe')
    for script in ['print("invalid json")', 'print("[]")', 'raise SystemExit(4)']:
        with pytest.raises(ConfigurationError, match='probe'):
            evaluate(f"run_json({[sys.executable, '-c', script]!r}) is None", values={}, bundle=bundle, invocation=invocation, location='probe')
    with pytest.raises(ConfigurationError, match='probe'):
        evaluate("run_json(['nonexistent-pspec-program']) is None", values={}, bundle=bundle, invocation=invocation, location='probe')


def test_which_uses_invocation_cwd_and_environment(tmp_path, bundle):
    folder = tmp_path / 'tools'; folder.mkdir()
    file = folder / ('probe.EXE' if os.name == 'nt' else 'probe')
    file.write_text('');file.chmod(0o755)
    invocation = Invocation(tmp_path, env={'PATH': 'tools', 'PATHEXT': '.EXE'})
    assert evaluate("which('probe') == vars['path']", values={'path': str(file)}, bundle=bundle, invocation=invocation, location='which')


def test_timeout_diagnostic_and_literal_argv(tmp_path, bundle):
    from powerspec.utils.processes import ProcessJSONError
    def timed_out(argv, **options):
        assert options['timeout'] == 5
        raise ProcessJSONError('timeout', 'controlled timeout')
    with pytest.raises(ConfigurationError, match='timeout'):
        evaluate("run_json(['probe']) is None", values={}, bundle=bundle,
                 invocation=Invocation(tmp_path, probe=timed_out), location='timed-trait')
    code = 'import json,sys;print(json.dumps({"arg":sys.argv[1]}))'
    literal = '$(not-a-command); & value'
    assert evaluate(f"run_json({[sys.executable, '-c', code, literal]!r})['arg'] == vars['literal']",
                    values={'literal': literal}, bundle=bundle, invocation=Invocation(tmp_path), location='literal')


def test_invocation_accepts_a_smaller_probe_timeout(tmp_path, bundle):
    calls = []
    def probe(argv, **options):
        calls.append((argv, options))
        return {'ok': True}
    invocation = Invocation(tmp_path, probe=probe, run_json_timeout=2)
    assert evaluate("run_json(['probe']).get('ok') is True", values={}, bundle=bundle,
                    invocation=invocation, location='bounded-trait')
    assert calls[0][1]['timeout'] == 2


@pytest.mark.parametrize('timeout', [0, -1, 5.1, float('inf'), float('nan'), True, '2'])
def test_invocation_rejects_invalid_probe_timeout(tmp_path, timeout):
    with pytest.raises(ValueError, match='run_json_timeout'):
        Invocation(tmp_path, run_json_timeout=timeout)


def test_armed_exclusions_shared_descendants_remote_and_fresh_snapshot(tmp_path):
    put(tmp_path, 'profiles/main.toml', 'profiles=["@builtin/child", "@builtin/shared"]')
    put(tmp_path, 'profiles/global.toml', 'global=true\nprofiles=["@builtin/child"]')
    put(tmp_path, 'profiles/child.toml', 'profiles=["@builtin/shared"]\ntraits=["@builtin/never"]')
    put(tmp_path, 'profiles/shared.toml', 'skills=["external/skills/*"]\n'
        '[[source]]\nid="external"\nprovider="git"\n'
        'origin="https://example.test/external"\nreference="main"')
    put(tmp_path, 'traits/never.toml', 'hooks=["sessionStart"]\nbody="never"\nwhen="missing()"')
    remote = tmp_path/'remote'
    put(remote, 'skills/tool/SKILL.md', '---\nname: tool\n---\n')
    catalog = Catalog(builtin=tmp_path, gitsources={'external': remote})
    first = compose(catalog, '@builtin/main', agent='codex', exclude_profiles=['@builtin/child'])
    assert first.armed('profile', '@builtin/global')
    assert first.armed('profile', '@builtin/shared')
    assert not first.armed('profile', '@builtin/child')
    assert not first.armed('trait', '@builtin/never')
    assert first.armed('skill', 'external/skills/tool')
    assert trait_contributions(first, None, Invocation(tmp_path), matching_refs=['@builtin/never']) == ()
    second = compose(catalog, '@builtin/main', agent='codex')
    assert second.armed('trait', '@builtin/never')
    assert not first.armed('trait', '@builtin/never')


def test_package_inspection_trait_follows_utility_bundle():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    with builtin_catalog_root() as catalog_root:
        catalog = Catalog(builtin=catalog_root)
        excluded = ['@builtin/zmem-lifecycle', '@builtin/adhd-friendly']
        selected = compose(catalog, '@builtin/python-simple-cli', agent='codex', exclude_profiles=excluded)
        ref = '@builtin/mature-package-inspection'
        result = trait_contributions(selected, None, Invocation(root), matching_refs=[ref])
        assert len(result) == 1 and 'reusable helpers' in result[0].body
        without = compose(catalog, '@builtin/python-simple-cli', agent='codex', exclude_profiles=[*excluded, '@builtin/utils-planning-aware'])
        assert trait_contributions(without, None, Invocation(root), matching_refs=[ref]) == ()


def test_context_compiles_declared_values_skills_and_distinct_ids_once(tmp_path):
    put(tmp_path, 'profiles/main.toml', 'contexts=["@builtin/example"]\nskills=["@builtin/helper"]\n[vars]\nvalue="<skill:missing>"')
    put(tmp_path, 'contexts/example.toml', '''
[[compiletime]]
id="value"
type="string"
[[attach.context]]
id="first"
body="Value <value>; skill <skill:helper>; literal <other>."
[[attach.context]]
body="Second."
''')
    put(tmp_path, 'skills/helper/SKILL.md', '---\nname: helper\n---\n')
    bundle = compose(Catalog(builtin=tmp_path), '@builtin/main', agent='codex')
    result = context_contributions(bundle, None, Invocation(tmp_path))
    assert [item.identifier for item in result] == [
        '@builtin/example/context/first', '@builtin/example/context/2'
    ]
    assert result[0].body == 'Value <skill:missing>; skill helper; literal <other>.'
    assert all(item.identifier != 'pspec' for item in result)
    bundle.contexts[0].data['attach']['context'][0]['body'] = '<skill:missing>'
    with pytest.raises(ConfigurationError, match='missing'):
        context_contributions(bundle, None, Invocation(tmp_path))


def test_trait_compiles_exact_deferred_remote_skill_without_acquisition(tmp_path):
    put(tmp_path, 'profiles/main.toml', '''
traits=["@builtin/reminder"]
skills=["external/skills/remote-skill"]
[[source]]
id="external"
provider="git"
origin="https://example.test/external"
reference="main"
''')
    put(tmp_path, 'traits/reminder.toml', '''
hooks=["sessionStart"]
body="Use <skill:remote-skill>."
''')
    selected = compose(Catalog(builtin=tmp_path), '@builtin/main', agent='codex',
                       resolve_remote_skills=False)
    result = trait_contributions(selected, None, Invocation(tmp_path),
                                 matching_refs=['@builtin/reminder'])
    assert result[0].body == 'Use remote-skill.'


def test_trait_compiles_name_covered_by_deferred_remote_wildcard(tmp_path):
    put(tmp_path, 'profiles/main.toml', '''
traits=["@builtin/reminder"]
skills=["external/skills/*"]
[[source]]
id="external"
provider="git"
origin="https://example.test/external"
reference="main"
''')
    put(tmp_path, 'traits/reminder.toml', '''
hooks=["sessionStart"]
body="Use <skill:remote-skill>."
''')
    selected = compose(Catalog(builtin=tmp_path), '@builtin/main', agent='codex',
                       resolve_remote_skills=False)
    result = trait_contributions(selected, None, Invocation(tmp_path),
                                 matching_refs=['@builtin/reminder'])
    assert result[0].body == 'Use remote-skill.'
