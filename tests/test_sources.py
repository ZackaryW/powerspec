from pathlib import Path
import pytest
from powerspec.catalog import ConfigurationError
from powerspec.sources import ExternalCatalogs, SourceBinding, discover_catalogs, milkpan_spec


@pytest.mark.parametrize('origin,same', [
    ('https://github.com/zackaryw/zmem.git', True),
    ('https://github.com/ZackaryW/zmem/', True),
    ('https://github.com/zackaryw/other', False),
])
def test_github_origins_canonicalize_to_one_milkpan_spec(origin, same):
    assert (milkpan_spec(origin) == milkpan_spec('https://github.com/ZackaryW/zmem')) is same


@pytest.mark.parametrize('origin', ['https://example.test/Owner/Repo', 'https://github.com/Owner/Repo?token=x',
                                    'ssh://git@github.com/owner/repo'])
def test_other_origins_are_rejected_before_milkpan(origin):
    with pytest.raises(ConfigurationError, match='milkpan supports'):
        milkpan_spec(origin)


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
