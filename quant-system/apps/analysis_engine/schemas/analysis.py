"""分析输出结构。"""

from __future__ import annotations

from datetime import datetime

from shared.schemas.base import BaseSchema


class KeyFactor(BaseSchema):
    name: str
    value: str
    weight: float


class AnalysisAgentOutput(BaseSchema):
    task_id: str
    analysis_id: str
    analysis_version: str
    exchange: str
    symbol: str
    timeframe: str
    analysis_time: datetime
    market_regime: str
    directional_bias: str
    confidence: float
    volatility_level: str
    liquidity_level: str
    key_factors: list[KeyFactor]
    risk_flags: list[str]
    preferred_strategy_types: list[str]
    rejected_strategy_types: list[str]
    summary: str
