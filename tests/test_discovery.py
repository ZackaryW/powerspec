from pathlib import Path
import pytest
from powerspec.utils.discovery import find_ancestor_file


def test_nearest_boundary_and_missing(tmp_path):
    leaf = tmp_path / "a" / "b"
    leaf.mkdir(parents=True)
    (tmp_path / "settings.ini").write_text("outer")
    assert find_ancestor_file(leaf, "settings.ini", boundary=tmp_path) == tmp_path / "settings.ini"
    (leaf.parent / "settings.ini").write_text("near")
    assert find_ancestor_file(leaf, "settings.ini", boundary=tmp_path) == leaf.parent / "settings.ini"
    assert find_ancestor_file(leaf, "absent", boundary=leaf.parent) is None
    assert find_ancestor_file(leaf, "settings.ini", boundary=leaf) is None


@pytest.mark.parametrize("relative", ["../outside", ".", "a/../../outside"])
def test_invalid_relative(tmp_path, relative):
    with pytest.raises(ValueError):
        find_ancestor_file(tmp_path, relative, boundary=tmp_path)


def test_absolute_and_outside_start(tmp_path):
    child = tmp_path / "child"
    child.mkdir()
    with pytest.raises(ValueError):
        find_ancestor_file(tmp_path, "x", boundary=child)
    with pytest.raises(ValueError):
        find_ancestor_file(child, tmp_path / "x", boundary=tmp_path)


def test_inspection_error_is_not_missing(tmp_path, monkeypatch):
    original = Path.stat
    def denied(path, *args, **kwargs):
        if path.name == "denied":
            raise PermissionError("no access")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "stat", denied)
    with pytest.raises(PermissionError):
        find_ancestor_file(tmp_path, "denied", boundary=tmp_path)


def test_symlink_cannot_escape_boundary(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.write_text("data")
    try:
        (root / "link").symlink_to(outside)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")
    with pytest.raises(ValueError):
        find_ancestor_file(root, "link", boundary=root)
