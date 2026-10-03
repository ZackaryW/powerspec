from pathlib import Path
from types import SimpleNamespace
import pytest
from powerspec.catalog import Catalog, ConfigurationError
from powerspec.consumer import discover_consumer, runtime_values, context_values
from powerspec.profiles import compose
from powerspec.resources import builtin_catalog_root


def put(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def test_nearest_and_openspec_invocations(tmp_path):
    (tmp_path / ".git").mkdir()
    outer = put(tmp_path / "openspec/.pspec/config.toml", '[vars]\nlabel="outer"')
    inner = put(tmp_path / "packages/inner/openspec/.pspec/config.toml", '[vars]\nlabel="inner"')
    start = inner.parent.parent / "changes/example"
    start.mkdir(parents=True)
    assert discover_consumer(start).config_path == inner
    assert discover_consumer(outer.parent).config_path == outer
    inner.write_text("invalid = [")
    with pytest.raises(ConfigurationError, match="config.toml"):
        discover_consumer(start)


def test_worktree_and_no_consumer_no_writes(tmp_path):
    (tmp_path / ".git").mkdir()
    put(tmp_path / "openspec/.pspec/config.toml", '[vars]\nouter=true')
    child = tmp_path / "worktree"
    child.mkdir()
    put(child / ".git", "gitdir: ignored-by-boundary-detection")
    before = {p.relative_to(tmp_path) for p in tmp_path.rglob("*")}
    assert discover_consumer(child) is None
    assert {p.relative_to(tmp_path) for p in tmp_path.rglob("*")} == before
    path = put(child / "openspec/.pspec/config.toml", "")
    assert discover_consumer(child).git_root == child
    assert discover_consumer(child).config_path == path


def test_runtime_layers_origins_and_isolation(tmp_path):
    (tmp_path / ".git").mkdir()
    put(tmp_path / "openspec/.pspec/config.toml", '[vars]\na="config"\nb="config"\n[_change.one]\na="config-one"\nb="config-one"\n[_change.two]\na="config-two"')
    put(tmp_path / "openspec/.pspec/current.toml", '[vars]\na="current"\nb="current"\n[_change.one]\na="current-one"')
    bundle = SimpleNamespace(selected_defaults={"c":"selected"}, global_defaults={"c":"global","d":"global"})
    consumer = discover_consumer(tmp_path)
    values, origins = runtime_values(consumer, bundle, change="one", defaults={"e":"fallback"})
    assert values == {"a":"current-one","b":"current","c":"selected","d":"global","e":"fallback"}
    assert "current.toml#_change.one" in origins["a"]
    assert runtime_values(consumer,bundle,change="two")[0]["a"] == "current"
    assert runtime_values(consumer,bundle)[0]["a"] == "current"
    assert runtime_values(consumer,bundle,change="unknown")[0]["a"] == "current"
    (tmp_path / "openspec/.pspec/current.toml").unlink()
    consumer = discover_consumer(tmp_path)
    assert runtime_values(consumer,bundle,change="one")[0]["a"] == "config-one"
    assert runtime_values(consumer,bundle)[0]["a"] == "config"
    assert runtime_values(None,bundle)[0] == {"c":"selected","d":"global"}


def test_context_ignores_even_malformed_current_and_change(tmp_path):
    (tmp_path / ".git").mkdir()
    config = put(tmp_path / "openspec/.pspec/config.toml", '[vars]\nutility_path="src/example/utils"\n[_change.one]\ncli_framework="invalid"')
    put(config.parent / "current.toml", "invalid = [")
    with pytest.raises(ConfigurationError, match="current.toml"):
        discover_consumer(tmp_path)
    consumer = discover_consumer(tmp_path, runtime=False)
    with builtin_catalog_root() as root:
        catalog = Catalog(builtin=root)
        bundle = compose(catalog,"@builtin/python-simple-cli",agent="codex",exclude_profiles=["@builtin/zmem-lifecycle","@builtin/adhd-friendly"])
        context = catalog.get("context","@builtin/python-simple-cli")
        values, origins = context_values(context,consumer,bundle)
        assert values["test_command"] == "uv run pytest"
        assert values["cli_framework"] == "typer"
        assert values["utility_path"] == "src/example/utils"
        assert origins["utility_path"].endswith("config.toml#vars")
        config.write_text('[vars]\nutility_path="utils"\ncli_framework="invalid"')
        with pytest.raises(ConfigurationError, match="cli_framework"):
            context_values(context,discover_consumer(tmp_path,runtime=False),bundle)
        with pytest.raises(ConfigurationError, match="utility_path"):
            context_values(context,None,bundle)
        config.write_text('[vars]\nutility_path="utils"')
        empty = SimpleNamespace(global_defaults={},selected_defaults={})
        assert context_values(context,discover_consumer(tmp_path,runtime=False),empty)[0]["test_command"] == "uv run pytest"


def test_two_consumers_do_not_share_answers(tmp_path):
    bundle = SimpleNamespace(selected_defaults={},global_defaults={})
    for name in ("one","two"):
        repo=tmp_path/name;repo.mkdir();(repo/".git").mkdir()
        put(repo/"openspec/.pspec/config.toml", f'[vars]\nlabel="{name}"')
    assert runtime_values(discover_consumer(tmp_path/"one"),bundle)[0] == {"label":"one"}
    assert runtime_values(discover_consumer(tmp_path/"two"),bundle)[0] == {"label":"two"}


def test_each_runtime_layer_and_compiletime_precedence(tmp_path):
    (tmp_path / '.git').mkdir()
    config = put(tmp_path / 'openspec/.pspec/config.toml', '[vars]\nx="config"')
    context = SimpleNamespace(ref='@local/example', path=tmp_path/'example.toml',
                              data={'compiletime': [{'id': 'x', 'type': 'string', 'default': 'declaration'}]})
    bundle = SimpleNamespace(selected_defaults={'x': 'selected'}, global_defaults={'x': 'global'})
    assert context_values(context, discover_consumer(tmp_path), bundle)[0]['x'] == 'config'
    config.write_text('')
    assert context_values(context, discover_consumer(tmp_path), bundle)[0]['x'] == 'selected'
    bundle.selected_defaults = {}
    assert runtime_values(None, bundle, defaults={'x': 'caller'})[0]['x'] == 'global'
    assert context_values(context, None, bundle)[0]['x'] == 'global'
    bundle.global_defaults = {}
    assert runtime_values(None, bundle, defaults={'x': 'caller'})[0]['x'] == 'caller'
    assert context_values(context, None, bundle)[0]['x'] == 'declaration'
    config.write_text('[vars]\nx=123')
    with pytest.raises(ConfigurationError, match='x'):
        context_values(context, discover_consumer(tmp_path), bundle)


def test_structural_errors_no_parent_or_sibling_fallback(tmp_path):
    (tmp_path / '.git').mkdir()
    put(tmp_path / 'sibling/openspec/.pspec/config.toml', '[vars]\nx=true')
    assert discover_consumer(tmp_path) is None
    config = put(tmp_path / 'openspec/.pspec/config.toml', 'vars=[]')
    with pytest.raises(ConfigurationError, match='config.toml'):
        discover_consumer(tmp_path)
    config.write_text('')
    put(config.parent / 'current.toml', 'profile="@builtin/invalid-in-current"')
    with pytest.raises(ConfigurationError, match='current.toml'):
        discover_consumer(tmp_path)
    assert discover_consumer(tmp_path, runtime=False).current is None
