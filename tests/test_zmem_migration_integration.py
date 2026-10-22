"""Recipe migration through real Saucepan retention and ZuAT ownership."""
from contextlib import contextmanager
import json
from pathlib import Path
import tempfile

import pytest
from saucepan_sdk import Client

from powerspec.catalog import MetadataUnavailable
from powerspec.installation import install_consumer
from powerspec.sources import SaucepanSources
from test_sources_integration import BINARY, git


@pytest.mark.skipif(not BINARY, reason='set SAUCEPAN_TEST_BINARY')
def test_new_origin_preserves_retention_matching_skills_and_native_edits(monkeypatch):
    import powerspec.workspace as workspace

    with tempfile.TemporaryDirectory(prefix='ps-zm-') as temporary:
        root = Path(temporary)
        names = ('zmem-query-memory', 'zmem-author-commits', 'zmem-design-extensions')
        origins = [root / 'old', root / 'new']
        for origin in origins:
            origin.mkdir()
            git(origin, 'init', '-b', 'main')
            git(origin, 'config', 'user.name', 'Test')
            git(origin, 'config', 'user.email', 'test@example.invalid')
            for name in names:
                skill = origin / 'skills' / name / 'SKILL.md'
                skill.parent.mkdir(parents=True)
                body = 'Same' if name == names[0] else origin.name
                skill.write_text(f'---\nname: {name}\ndescription: Memory workflow.\n---\n\n{body}\n')
            git(origin, 'add', '.')
            git(origin, 'commit', '-m', origin.name)
        project = root / 'project'
        config = project / 'openspec/.pspec/config.toml'
        config.parent.mkdir(parents=True)
        (project / '.git').mkdir()
        config.write_text('[vars]\n')
        builtin = root / 'builtin'
        profile = builtin / 'profiles/zmem-lifecycle.toml'
        profile.parent.mkdir(parents=True)
        def select(origin):
            profile.write_text('global=true\nscope="user"\nskills=["zmem/skills/*"]\n'
                '[[source]]\nid="zmem"\nprovider="git"\n'
                f'origin={json.dumps(str(origin))}\nreference="main"\n')
        @contextmanager
        def resources():
            yield builtin
        monkeypatch.setattr(workspace, 'builtin_catalog_root', resources)
        client = Client(executable=BINARY, root=str(root / 'store'))
        store = SaucepanSources(client, consumer_path=config)
        home = root / 'home'
        options = dict(agent='codex', home=home, registry=root / 'registry', source_store=store)
        old_recipe, new_recipe = [dict(provider='git', origin=str(origin), reference='main') for origin in origins]
        select(origins[0])
        assert install_consumer(project, **options).ok
        retained = store.lookup('zmem', old_recipe)
        skills = home / '.codex/skills'
        matching = skills / names[0] / 'SKILL.md'
        unchanged = matching.read_bytes(), matching.stat().st_mtime_ns
        edited = skills / names[2] / 'SKILL.md'
        baseline = edited.read_bytes()
        edited.write_bytes(baseline + b'User edit\n')
        user_bytes = edited.read_bytes()
        hooks = home / '.codex/hooks.json'
        hook_bytes = hooks.read_bytes()

        select(origins[1])
        with pytest.raises(MetadataUnavailable, match='no selected materialization'):
            store.lookup('zmem', new_recipe)
        blocked = install_consumer(project, **options)
        assert not blocked.ok
        outcomes = {item.plan.name: item.status for item in blocked.provisioning.items}
        assert outcomes == {names[0]: 'reused', names[1]: 'updated', names[2]: 'failed'}
        assert edited.read_bytes() == user_bytes
        assert (matching.read_bytes(), matching.stat().st_mtime_ns) == unchanged
        assert hooks.read_bytes() == hook_bytes
        assert store.lookup('zmem', old_recipe) == retained
        with pytest.raises(MetadataUnavailable):
            store.lookup('zmem', new_recipe)

        # The fixture owner explicitly restores its edit; init never authorizes it.
        edited.write_bytes(baseline)
        assert install_consumer(project, **options).ok
        selected = store.lookup('zmem', new_recipe)
        assert selected.repository == str(origins[1])
        assert selected.resolved_revision == git(origins[1], 'rev-parse', 'HEAD')
        assert store.lookup('zmem', old_recipe) == retained
        assert (matching.read_bytes(), matching.stat().st_mtime_ns) == unchanged
        assert hooks.read_bytes() == hook_bytes
        assert edited.read_text().endswith('new\n')
