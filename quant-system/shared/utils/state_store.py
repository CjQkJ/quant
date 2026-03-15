"""运行状态存储抽象。"""

from __future__ import annotations

import json
from typing import Any, Protocol


class StateStore(Protocol):
    def get_json(self, key: str, default: Any = None) -> Any:
        ...

    def set_json(self, key: str, value: Any) -> None:
        ...

    def get_bool(self, key: str, default: bool = False) -> bool:
        ...

    def set_bool(self, key: str, value: bool) -> None:
        ...


class InMemoryStateStore:
    """测试和本地降级使用的状态存储。"""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def get_json(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set_json(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get_bool(self, key: str, default: bool = False) -> bool:
        return bool(self._data.get(key, default))

    def set_bool(self, key: str, value: bool) -> None:
        self._data[key] = bool(value)


class RedisStateStore:
    """Redis 状态存储。"""

    def __init__(self, redis_url: str) -> None:
        try:
            import redis
        except ModuleNotFoundError as exc:  # pragma: no cover - 依赖缺失时只在运行期触发
            raise RuntimeError("未安装 redis 依赖，无法使用 RedisStateStore") from exc

        self._client = redis.Redis.from_url(redis_url, decode_responses=True)

    def get_json(self, key: str, default: Any = None) -> Any:
        value = self._client.get(key)
        if value is None:
            return default
        return json.loads(value)

    def set_json(self, key: str, value: Any) -> None:
        self._client.set(key, json.dumps(value))

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self._client.get(key)
        if value is None:
            return default
        return value == "1"

    def set_bool(self, key: str, value: bool) -> None:
        self._client.set(key, "1" if value else "0")

