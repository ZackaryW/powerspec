from pathlib import Path
import pytest
from powerspec.utils.layers import overlay_layers


def test_native_shallow_values_and_origins():
    original = {"path": Path("here"), "nested": {"a": 1}, "nullable": "old"}
    override = {"nested": {"b": 2}, "nullable": None}
    values, origins = overlay_layers([("base", original), ("override", override)])
    assert values == {"path": Path("here"), "nested": {"b": 2}, "nullable": None}
    assert origins == {"path": "base", "nested": "override", "nullable": "override"}
    assert original["nested"] == {"a": 1}
    assert values["nested"] is override["nested"]
    values["new"] = 3
    assert "new" not in original and "new" not in override


def test_empty_and_duplicate_layers():
    assert overlay_layers([]) == ({}, {})
    with pytest.raises(ValueError, match="duplicate"):
        overlay_layers([("base", {}), ("base", {})])
