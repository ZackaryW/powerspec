import pytest

from powerspec.catalog import ConfigurationError
from powerspec.progress import lifecycle_progress
from powerspec.sources import MilkpanSources

from milkpan_fake import FakeMilkpan

RECIPE = {'provider': 'git', 'origin': 'https://github.com/octo/tools', 'reference': 'main'}


@pytest.fixture
def retained(tmp_path):
    client = FakeMilkpan(tmp_path / 'milkpan')
    client.refs['github:octo/tools@main'] = 'a' * 40
    config = tmp_path / 'consumer/openspec/.pspec/config.toml'
    config.parent.mkdir(parents=True)
    store = MilkpanSources(client, consumer_path=config)
    store.ensure('tools', RECIPE)
    store.commit()
    return store, client


def test_retained_reuse_is_reported_only_after_validation(retained):
    store, client = retained
    events = []
    with lifecycle_progress(events.append):
        store.ensure('tools', RECIPE)
    assert any(e.state == 'reused' and 'no refresh' in e.detail for e in events)
    assert not any('Materializing' in e.label for e in events)
    client.leases_by_id.clear()
    events.clear()
    with lifecycle_progress(events.append), pytest.raises(ConfigurationError):
        store.ensure('tools', RECIPE)
    assert not any(e.state == 'reused' for e in events)


def test_source_library_without_observer_stays_silent(retained, capsys):
    store, _ = retained
    store.ensure('tools', RECIPE)
    assert capsys.readouterr() == ('', '')
