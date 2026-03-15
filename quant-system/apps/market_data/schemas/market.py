"""市场数据结构。"""

from __future__ import annotations

from datetime import datetime

from shared.schemas.base import BaseSchema


class OHLCVPayload(BaseSchema):
    exchange: str
    symbol: str
    timeframe: str
    open_time: datetime
    close_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float
    trade_count: int | None = None
    source: str


class OrderLevel(BaseSchema):
    price: float
    qty: float


class OrderBookSnapshotPayload(BaseSchema):
    exchange: str
    symbol: str
    snapshot_time: datetime
    best_bid: float
    best_ask: float
    bid_depth: list[OrderLevel]
    ask_depth: list[OrderLevel]
    spread: float
    source: str


class TradeTickPayload(BaseSchema):
    exchange: str
    symbol: str
    trade_id: str
    trade_time: datetime
    price: float
    qty: float
    side: str
    is_buyer_maker: bool | None = None
    source: str


class DerivativesMetricPayload(BaseSchema):
    exchange: str
    symbol: str
    metric_time: datetime
    metric_type: str
    metric_value: float
    extra_json: dict | None = None
    source: str

