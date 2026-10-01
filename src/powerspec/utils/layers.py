"""Shallow named overlays with provenance, independent of application policy."""
from collections.abc import Iterable, Mapping


def overlay_layers(layers: Iterable[tuple[str, Mapping]]) -> tuple[dict, dict]:
    """Later mappings win. Preserve native values and reject ambiguous origins."""
    values, origins = {}, {}
    seen = set()
    for name, mapping in layers:
        if name in seen:
            raise ValueError(f"duplicate layer name: {name}")
        seen.add(name)
        for key, value in mapping.items():
            values[key] = value
            origins[key] = name
    return values, origins
