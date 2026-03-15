"""简单重试工具。"""

from __future__ import annotations

from collections.abc import Callable
from time import sleep
from typing import TypeVar


T = TypeVar("T")


def retry_call(
    func: Callable[[], T],
    retries: int = 3,
    delay_seconds: float = 0.1,
    retry_exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    last_error: BaseException | None = None
    for attempt in range(retries):
        try:
            return func()
        except retry_exceptions as exc:  # pragma: no cover - 分支由测试覆盖
            last_error = exc
            if attempt == retries - 1:
                break
            sleep(delay_seconds)
    assert last_error is not None
    raise last_error

