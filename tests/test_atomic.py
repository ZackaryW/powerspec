import os
from pathlib import Path
import tempfile

import pytest

from powerspec.utils.atomic import AtomicWriteError, replace_bytes


def test_replace_bytes_writes_once_and_skips_identical_content(tmp_path):
    target = tmp_path / "config.toml"
    assert replace_bytes(target, b"profile = 'one'\n") is True
    first = target.stat().st_mtime_ns
    assert replace_bytes(target, b"profile = 'one'\n") is False
    assert target.stat().st_mtime_ns == first
    assert replace_bytes(target, b"profile = 'two'\n") is True
    assert target.read_bytes() == b"profile = 'two'\n"
    assert set(tmp_path.iterdir()) == {target}


def test_replace_bytes_preserves_original_and_cleans_staging_on_failure(tmp_path, monkeypatch):
    target = tmp_path / "config.toml"
    target.write_bytes(b"original")
    import powerspec.utils.atomic as atomic

    def fail(source: Path, destination: Path) -> None:
        raise OSError("controlled failure")

    monkeypatch.setattr(atomic.os, "replace", fail)
    with pytest.raises(AtomicWriteError, match="controlled failure"):
        replace_bytes(target, b"candidate")
    assert target.read_bytes() == b"original"
    assert set(tmp_path.iterdir()) == {target}


def test_replace_bytes_at_supported_path_boundary(tmp_path):
    # Exercise MAX_PATH on legacy Windows and the usual component limit elsewhere.
    name_length = min(250, 256 - len(str(tmp_path)) - 1) if os.name == "nt" else 250
    if name_length < 32:
        pytest.skip("temporary root leaves insufficient room for a long filename")
    target = tmp_path / ("a" * name_length)
    # Independently establish that the destination and a short sibling are valid.
    target.write_bytes(b"probe")
    with tempfile.TemporaryFile(dir=tmp_path):
        pass
    target.unlink()

    assert replace_bytes(target, b"first") is True
    assert target.read_bytes() == b"first"
    assert replace_bytes(target, b"updated") is True
    assert target.read_bytes() == b"updated"
    modified = target.stat().st_mtime_ns
    assert replace_bytes(target, b"updated") is False
    assert target.stat().st_mtime_ns == modified
    assert set(tmp_path.iterdir()) == {target}


def test_replace_bytes_requires_existing_parent(tmp_path):
    with pytest.raises(AtomicWriteError, match="parent"):
        replace_bytes(tmp_path / "missing/config.toml", b"value")
