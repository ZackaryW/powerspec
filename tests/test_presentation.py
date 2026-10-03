from dataclasses import dataclass
import json
from pathlib import Path

from powerspec.presentation import json_text, to_data


@dataclass(frozen=True)
class Result:
    path: Path
    values: tuple[str, ...]
    ok: bool = True


def test_structured_results_convert_to_one_stable_json_value(tmp_path):
    result = Result(tmp_path / "config.toml", ("one", "two"))
    data = to_data(result)
    assert data == {
        "path": str(tmp_path / "config.toml"),
        "values": ["one", "two"],
        "ok": True,
    }
    rendered = json_text(result)
    assert rendered.count("\n") == 0
    assert json.loads(rendered) == data
