import pytest

from powerspec.catalog import ConfigurationError
from powerspec.progress import lifecycle_progress
from test_sources import retained


def test_retained_reuse_is_reported_only_after_validation(retained):
    store, recipe, client, _ = retained
    events = []
    with lifecycle_progress(events.append):
        store.ensure('tools', recipe)
    assert any(e.state == 'reused' and 'no refresh' in e.detail for e in events)
    assert not any('Materializing' in e.label for e in events)
    client.receipt['state'] = 'released'
    events.clear()
    with lifecycle_progress(events.append), pytest.raises(ConfigurationError):
        store.ensure('tools', recipe)
    assert not any(e.state == 'reused' for e in events)


def test_source_library_without_observer_stays_silent(retained, capsys):
    store, recipe, _, _ = retained
    store.ensure('tools', recipe)
    assert capsys.readouterr() == ('', '')
