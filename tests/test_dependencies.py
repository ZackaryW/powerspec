import pytest
from powerspec.utils.dependencies import dependency_order


def test_diamond_repeats_and_order():
    graph = {"a": ["b", "c"], "b": ["d"], "c": ["d"], "d": [], "z": []}
    assert dependency_order(["a", "z", "a"], graph) == ("d", "b", "c", "a", "z")
    assert dependency_order(["z", "a"], graph) == ("z", "d", "b", "c", "a")
    assert dependency_order([], graph) == ()


@pytest.mark.parametrize("graph,match", [({"a": ["missing"]}, "a.*missing"), ({"a": ["a"]}, "a.*a"), ({"a": ["b"], "b": ["a"]}, "a.*b.*a")])
def test_bad_graph_has_path(graph, match):
    with pytest.raises(ValueError, match=match):
        dependency_order(["a"], graph)


def test_long_chain_does_not_depend_on_python_recursion_limit():
    graph = {i: [i + 1] for i in range(1500)}
    graph[1500] = []
    assert dependency_order([0], graph) == tuple(reversed(range(1501)))
