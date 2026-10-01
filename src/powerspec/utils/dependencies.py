"""Stable dependency-first traversal over caller-owned identifiers."""
from collections.abc import Hashable, Iterable, Mapping, Sequence


def dependency_order[T: Hashable](roots: Iterable[T], dependencies: Mapping[T, Sequence[T]]) -> tuple[T, ...]:
    """Return each reachable node once, or raise with a missing/cycle path.

    Explicit stacks keep graph depth independent of Python's recursion limit.
    Supplied root and edge ordering determine otherwise independent ordering.
    """
    done: set[T] = set()
    result: list[T] = []
    active: list[T] = []
    positions: dict[T, int] = {}
    for root in roots:
        stack = [(root, False)]
        while stack:
            node, leaving = stack.pop()
            if leaving:
                active.pop()
                del positions[node]
                done.add(node)
                result.append(node)
                continue
            if node in done:
                continue
            if node in positions:
                cycle = active[positions[node]:] + [node]
                raise ValueError("dependency cycle: " + " -> ".join(map(str, cycle)))
            if node not in dependencies:
                raise ValueError("missing dependency: " + " -> ".join(map(str, active + [node])))
            positions[node] = len(active)
            active.append(node)
            stack.append((node, True))
            stack.extend((child, False) for child in reversed(dependencies[node]))
    return tuple(result)
