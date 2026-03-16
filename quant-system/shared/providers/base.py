"""市场、执行、账户 provider 抽象。"""

from __future__ import annotations

from typing import Protocol

from apps.execution_engine.schemas.execution import PaperAccountSnapshot, PlannedOrder


class MarketDataProvider(Protocol):
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 200) -> list[dict]:
        ...

    def fetch_order_book(self, symbol: str, depth: int = 20) -> dict:
        ...


class ExecutionProvider(Protocol):
    market_type: str
    account_mode: str

    def submit_orders(self, planned_orders: list[PlannedOrder]) -> dict:
        ...


class AccountProvider(Protocol):
    market_type: str
    account_mode: str

    def get_account_snapshot(self) -> PaperAccountSnapshot:
        ...
