"""历史回放数据加载。"""

from __future__ import annotations

import json
from pathlib import Path


class ReplayLoader:
    def load_json(self, path: str | Path) -> list[dict]:
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle)

