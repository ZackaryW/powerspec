from pathlib import Path
import pytest
from powerspec.catalog import ConfigurationError
from powerspec.sources import ExternalCatalogs, SourceBinding, discover_catalogs

def binding(identity, root, revision="a" * 40):
    return SourceBinding(identity, "https://example.test/tools", "main", revision,
                         "1" * 64, "artifact", root)


def write(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_catalog_discovery_includes_nested_reusable_roots_and_excludes_consumers(tmp_path):
    public = tmp_path / ".pspec"
    nested = tmp_path / "packages/tool/.pspec"
    private = tmp_path / "openspec/.pspec"
    for root in (public, nested, private):
        write(root, "profiles/base.toml", 'scope="user"')
    assert discover_catalogs(tmp_path) == (public.resolve(), nested.resolve())


def test_catalog_discovery_rejects_absence_and_escape(tmp_path):
    with pytest.raises(ConfigurationError, match="no reusable"):
        discover_catalogs(tmp_path)
    outside = tmp_path.parent / "external-catalog"
    write(outside, "profiles/base.toml", 'scope="user"')
    link = tmp_path / ".pspec"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(str(error))
    with pytest.raises(ConfigurationError, match="escapes"):
        discover_catalogs(tmp_path)


def test_external_registration_is_validated_atomic_and_reserves_builtin(tmp_path):
    good = tmp_path / "good"
    write(good, ".pspec/profiles/base.toml", 'scope="user"')
    registry = ExternalCatalogs().register(binding("team", good))
    assert tuple(registry.bindings) == ("team",)

    bad = tmp_path / "bad"
    write(bad, ".pspec/profiles/base.toml", 'scope="broken"')
    with pytest.raises(ConfigurationError, match="base.toml"):
        registry.register(binding("team", bad, "b" * 40))
    assert registry.bindings["team"].source.root == good

    absent = tmp_path / "absent"
    absent.mkdir()
    with pytest.raises(ConfigurationError, match="no reusable"):
        registry.register(binding("team", absent))
    assert registry.bindings["team"].source.root == good

    with pytest.raises(ConfigurationError, match="reserved"):
        registry.register(binding("builtin", good))


@pytest.fixture
def retained(tmp_path):
    import copy
    from powerspec.sources import SaucepanSources
    source = {"provider": "git", "origin": "https://example.test/tools", "reference": "main"}
    root = tmp_path / "output"
    root.mkdir()
    (root / "resource").write_text("retained")
    calls = []
    class Client:
        def for_app(self, app, **options):
            assert app == 'app'
            return self
        def pin(self, uuid):
            calls.append('pin')
            return copy.deepcopy(self.receipt)
        def __getattr__(self, method):
            raise AssertionError(f'lookup attempted {method}')
    client = Client()
    store = SaucepanSources(client, consumer_path=tmp_path / 'consumer/config.toml')
    target = {'type': 'acquire', 'source_uuid': 'source', 'selector': {'type': 'ref', 'reference': 'main'}}
    client.receipt = {'owner': 'app', 'state': 'active', 'outputs': {'out': {'available': True, 'path': str(root)}},
        'group': {'group': {'uuid': 'group', 'definition': {'members': [{'target': target}]},
            'selected': {'members': {'repository': {'scope': store.scope, 'output_uuid': 'out',
                'relative': None, 'selected_source': {'type': 'git', 'commit': 'a' * 40}}}}}}}
    recipe = store._source('tools', source)
    state = store._state()
    state['app'] = 'app'
    state['selected'][store._key(recipe)] = {'recipe': source, 'pin': 'pin', 'output': 'out',
        'group': 'group', 'source': 'source', 'commit': 'a' * 40}
    store._write(state)
    return store, source, client, calls


def test_readonly_retained_lookup_aliases_and_provenance(retained):
    store, source, client, calls = retained
    before = store.state_path.read_bytes()
    first = store.lookup('tools', source)
    second = store.lookup('other-alias', source)
    assert first.artifact_id == second.artifact_id
    assert first.resolved_revision == 'a' * 40
    assert (first.root / 'resource').read_text() == 'retained'
    assert calls == ['pin', 'pin']
    assert store.state_path.read_bytes() == before


@pytest.mark.parametrize('field,value', [('scope', 'another-consumer'), ('output_uuid', 'wrong'),
    ('relative', '../')])
def test_retained_lookup_rejects_foreign_or_escaping_view(retained, field, value):
    store, source, client, calls = retained
    member = client.receipt['group']['group']['selected']['members']['repository']
    member[field] = value
    with pytest.raises(ConfigurationError):
        store.lookup('tools', source)


def test_retained_lookup_rejects_mismatched_selector(retained):
    store, source, client, calls = retained
    client.receipt['group']['group']['definition']['members'][0]['target']['selector']['reference'] = 'other'
    with pytest.raises(ConfigurationError, match='provenance'):
        store.lookup('tools', source)


def test_readonly_denial_does_not_retry_unbound(retained):
    from saucepan_sdk import SaucepanError
    store, source, client, calls = retained
    def denied(uuid):
        calls.append('denied')
        raise SaucepanError('access_denied', 'no', {})
    client.pin = denied
    with pytest.raises(ConfigurationError, match='access_denied'):
        store.lookup('tools', source)
    assert calls == ['denied']


def test_readonly_deadline_exhaustion_never_calls_manager(retained):
    store, source, client, calls = retained
    with pytest.raises(ConfigurationError, match='budget'):
        store.lookup('tools', source, deadline=0)
    assert calls == []


def test_moved_consumer_is_not_silently_rebound(retained, tmp_path):
    import shutil
    store, source, client, calls = retained
    moved = store.for_consumer(tmp_path / 'moved/config.toml')
    moved.state_path.parent.mkdir()
    shutil.copyfile(store.state_path, moved.state_path)
    with pytest.raises(ConfigurationError, match='moved'):
        moved.lookup('tools', source)


def test_consumer_mutations_refuse_concurrent_writer(retained):
    store, source, client, calls = retained
    with store._mutation():
        with pytest.raises(ConfigurationError, match='already in progress'):
            with store._mutation():
                pytest.fail('lock bypassed')
    assert not store.state_path.with_suffix('.lock').exists()


def test_existing_ensure_is_readonly(retained):
    store, source, client, calls = retained
    assert store.ensure('alias', source).identity == 'alias'
    assert calls == ['pin']


@pytest.mark.parametrize('refresh', [False, True])
def test_preparation_keeps_manager_expansion_for_uncertain_retry(tmp_path, monkeypatch, refresh):
    import copy
    from saucepan_sdk import TransportError
    from powerspec.sources import SaucepanSources

    class Manager:
        def __init__(self):
            self.expansions = []
            self.registered = []

        def profile(self, name, **options):
            self.expansions.append((name, options))
            # Deliberately not the built-in IDs: the caller must consume the
            # manager's expansion instead of hard-coding the recipe locally.
            return {'catalog': [{'uuid': 'manager-policy', 'type': 'cache_policy', 'mode': 'cached'}],
                    'combined_policy_refs': ['manager-policy']}

        def register_policies(self, records):
            self.registered.append(copy.deepcopy(records))

        def register_source(self, source):
            return {'uuid': 'source', 'source': source}

        def query_claims(self, request):
            return {'claims': [], 'revision': 0}

        def list_groups(self, **options):
            raise TransportError('timeout', started=True, indeterminate=True)

    manager = Manager()
    store = SaucepanSources(manager, consumer_path=tmp_path / 'consumer/config.toml')
    def application(state):
        state['app'] = 'app'
        return manager
    monkeypatch.setattr(store, '_application', application)
    recipe = {'provider': 'git', 'origin': 'https://example.test/tools', 'reference': 'main'}
    operation = store.acquire if refresh else store.ensure
    with pytest.raises(ConfigurationError, match='timeout'):
        operation('tools', recipe)
    pending = copy.deepcopy(store._state()['pending'])
    with pytest.raises(ConfigurationError, match='timeout'):
        operation('tools', recipe)
    assert store._state()['pending'] == pending
    assert len(manager.expansions) == 1
    name, options = manager.expansions[0]
    assert name == 'explicit-update'
    if refresh:
        assert len(options['catalog']) == 1
        override = options['catalog'][0]
        assert override['type'] == 'update_policy' and override['mode'] == 'always'
        assert options['acquisition_policy_refs'] == [override['uuid']]
    else:
        assert options == {}
    intent = next(iter(pending.values()))['policies']
    assert intent['policy_refs'] == ['manager-policy']
    assert intent['catalog'][0]['uuid'] == 'manager-policy'
    assert intent['catalog'][-1]['type'] == 'pin_policy'
    assert intent['pin_refs'] == [intent['catalog'][-1]['uuid']]
    assert manager.registered == [intent['catalog'], intent['catalog']]


def test_default_client_uses_remaining_lookup_deadline(retained, monkeypatch):
    import powerspec.sources as module
    import powerspec.saucepan_tool as binary
    store, source, client, calls = retained
    store._client = None
    clock = [10.0]
    allowances = []
    monkeypatch.setattr(binary, 'monotonic', lambda: clock[0])
    def inspect(**options):
        assert options['deadline'] == 11.0
        clock[0] += .2
        return store.consumer_path.parent / 'saucepan.exe'
    def factory(**options):
        if 'timeout' in options:
            allowances.append(options['timeout'])
        return client
    monkeypatch.setattr(module, 'inspect_saucepan_binary', inspect)
    monkeypatch.setattr(module, 'Client', factory)
    monkeypatch.setattr(module, 'ensure_saucepan_binary', lambda: pytest.fail('lookup provisioned binary'))
    store.lookup('tools', source, deadline=11.0)
    assert allowances == pytest.approx([.8])


def test_corrupt_state_is_not_repaired(retained):
    store, source, client, calls = retained
    store.state_path.write_text('{bad')
    with pytest.raises(ConfigurationError, match='invalid Saucepan binding state'):
        store.ensure('tools', source)
    assert calls == [] and store.state_path.read_text() == '{bad'


@pytest.mark.parametrize('code', ['revision_conflict', 'integrity_error', 'key_unavailable', 'unknown_output'])
def test_structured_read_failures_are_preserved(retained, code):
    from saucepan_sdk import SaucepanError
    store, source, client, calls = retained
    def failure(uuid):
        raise SaucepanError(code, 'not interpreted', {})
    client.pin = failure
    with pytest.raises(ConfigurationError, match=code):
        store.lookup('tools', source)


def test_publication_failure_preserves_previous_bytes(retained, monkeypatch):
    store, source, client, calls = retained
    recipe = store._source('tools', source)
    key = store._key(recipe)
    state = store._state()
    candidate = {**state['selected'][key], 'key': 'new-generation'}
    state['pending'][key] = candidate
    store._write(state)
    before = store.state_path.read_bytes()
    store._candidates[key] = candidate
    def fail(*args):
        raise OSError('disk full')
    monkeypatch.setattr('powerspec.sources.replace_bytes', fail)
    with pytest.raises(OSError, match='disk full'):
        store.commit()
    assert store.state_path.read_bytes() == before


def test_exact_commit_selector_and_mismatch_are_checked(retained):
    store, source, client, calls = retained
    exact = {**source, 'reference': 'b' * 40}
    recipe = store._source('tools', exact)
    assert store._selector(recipe) == {'type': 'commit', 'commit': 'b' * 40}
    state = store._state()
    record = next(iter(state['selected'].values())).copy()
    record['recipe'] = exact
    state['selected'][store._key(recipe)] = record
    store._write(state)
    target = client.receipt['group']['group']['definition']['members'][0]['target']
    target['selector'] = store._selector(recipe)
    with pytest.raises(ConfigurationError, match='requested commit'):
        store.lookup('tools', exact)


def test_explicit_moved_rebind_preserves_old_receipts(retained, tmp_path):
    import shutil
    store, source, client, calls = retained
    moved = store.for_consumer(tmp_path / 'moved/config.toml')
    moved.state_path.parent.mkdir()
    shutil.copyfile(store.state_path, moved.state_path)
    backup = moved.state_path.with_name('previous-saucepan-receipts.json')
    moved.state_path.rename(backup)
    assert moved._state()['selected'] == {}
    assert moved.scope != store.scope
    assert backup.read_bytes() == store.state_path.read_bytes()
