"""分析引擎使用的市场特征。"""

from __future__ import annotations

from datetime import datetime

from shared.schemas.base import BaseSchema


class MarketFeatureSnapshot(BaseSchema):
    exchange: str
    symbol: str
    timeframe: str
    as_of: datetime
    last_price: float
    recent_return: float
    realized_volatility: float
    funding_rate: float
    open_interest: float
    spread_bps: float
    liquidity_score: float
    best_bid: float
    best_ask: float
    source_freshness_seconds: float

