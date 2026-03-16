"""策略运行信号结构。"""

from __future__ import annotations

from datetime import datetime

from shared.schemas.base import BaseSchema


class StrategySignal(BaseSchema):
    signal_id: str
    task_id: str
    analysis_id: str
    selection_id: str
    strategy_id: str
    symbol: str
    timeframe: str
    market_type: str
    signal_time: datetime
    action: str
    direction: str
    strength: float
    target_position_ratio: float
    reason: str
    risk_tags: list[str]
    strategy_runtime_version: str
