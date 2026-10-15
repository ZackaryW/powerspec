from powerspec.saucepan_tool import _compatible


def test_only_current_manager_protocol_is_compatible():
    assert _compatible('0.9.0+local')
    assert not _compatible('0.6.9')


def test_explicit_consumer_scope_is_required_for_remote_sources(tmp_path):
    from powerspec.sources import SaucepanSources
    first = SaucepanSources(object(), consumer_path=tmp_path / 'one/config.toml')
    second = SaucepanSources(object(), consumer_path=tmp_path / 'two/config.toml')
    assert first.scope != second.scope
    assert not (tmp_path / 'one').exists()
