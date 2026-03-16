"""策略相关结构。"""

from __future__ import annotations

from shared.schemas.base import BaseSchema


class StrategyMetadataSchema(BaseSchema):
    strategy_id: str
    strategy_name: str
    strategy_type: str
    description: str
    supported_exchange: str
    supported_symbol: str
    supported_timeframe: str
    market_regime_fit: list[str]
    directional_fit: list[str]
    risk_level: str
    max_position_ratio: float
    leverage_allowed: bool
    cooldown_seconds: int
    disable_conditions: list[str] | None = None
    priority: int = 0
    enabled: bool = True
    version: str = "v1"


class RankedCandidate(BaseSchema):
    strategy_id: str
    strategy_name: str
    fit_score: float
    reason: str
    strategy_type: str


class StrategySelectionOutput(BaseSchema):
    task_id: str
    analysis_id: str
    selection_id: str
    selection_time: str
    ranking_version: str
    selected_strategy_id: str
    selected_strategy_name: str
    selected_strategy_type: str
    fit_score: float
    candidate_strategies: list[RankedCandidate]
    fallback_strategy_id: str | None = None
    selection_reason: str
    constraints_checked: list[str]
    switch_attempted: bool = False
    cooldown_applied: bool = False
    selection_policy_note: str = "normal"
