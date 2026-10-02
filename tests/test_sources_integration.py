"""Opt-in acceptance test against the real pinned Saucepan CLI/SDK."""
import os
from pathlib import Path
import subprocess
import tempfile

import pytest
from saucepan_sdk import Saucepan

from powerspec.sources import SaucepanSources


BINARY = os.environ.get("SAUCEPAN_TEST_BINARY")
pytestmark = pytest.mark.skipif(not BINARY, reason="set SAUCEPAN_TEST_BINARY for real Saucepan acceptance")


def git(repo: Path, *args):
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def test_registered_app_identity_materializes_and_refreshes_complete_repository():
    # Saucepan documents short test roots as required on Windows.
    with tempfile.TemporaryDirectory(prefix="ps-sp-") as temporary:
        root = Path(temporary)
        repo = root / "src"
        repo.mkdir()
        git(repo, "init", "-b", "main")
        git(repo, "config", "user.name", "Powerspec Test")
        git(repo, "config", "user.email", "powerspec@example.test")
        (repo / "resource.txt").write_text("one", encoding="utf-8")
        git(repo, "add", "resource.txt")
        git(repo, "commit", "-m", "first")
        first_revision = git(repo, "rev-parse", "HEAD")

        base = Saucepan(binary=BINARY, test_root=root / "store", test_key="12" * 32)
        base.init()
        token = base.register("tools")
        app = base.for_app(token)
        recipe = {"source": {"provider": "git", "origin": str(repo), "reference": "main"}}
        initial = app.acquire(recipe)
        assert initial["artifact"]["revision"] == first_revision

        sources = SaucepanSources(base)
        observed = sources.lookup("tools")
        assert observed.resolved_revision == first_revision
        assert (observed.root / "resource.txt").read_text(encoding="utf-8") == "one"

        (repo / "resource.txt").write_text("two", encoding="utf-8")
        git(repo, "commit", "-am", "second")
        second_revision = git(repo, "rev-parse", "HEAD")
        refreshed = sources.acquire("tools")
        assert refreshed.resolved_revision == second_revision
        assert refreshed.source_id == observed.source_id
        assert (refreshed.root / "resource.txt").read_text(encoding="utf-8") == "two"
