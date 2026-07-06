from __future__ import annotations

from pathlib import Path
from typing import Any

import orjson


def dumps_json(data: Any) -> bytes:
    return orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(dumps_json(data))


def read_json(path: Path) -> Any:
    return orjson.loads(path.read_bytes())
