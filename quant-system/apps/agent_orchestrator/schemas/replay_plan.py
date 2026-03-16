"""回放规划结构。"""

from __future__ import annotations

from datetime import datetime

from shared.schemas.base import BaseSchema


class VersionTarget(BaseSchema):
    analysis_version: str
    ranking_version: str
    risk_policy_version: str
    strategy_runtime_version: str
    reason: str


class ReplayPlannerInput(BaseSchema):
    symbol: str = "BTCUSDT"
    timeframe: str = "5m"
    fixture_name: str = "replay_bars.json"


class ReplayPlannerOutput(BaseSchema):
    plan_id: str
    plan_time: datetime
    symbol: str
    timeframe: str
    fixture_name: str
    baseline: VersionTarget
    comparison_targets: list[VersionTarget]
    summary: str
