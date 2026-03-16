"""策略运行时基础抽象。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from apps.market_data.schemas.feature import MarketFeatureSnapshot
from apps.strategy_registry.schemas.strategy import StrategySelectionOutput
from shared.models.tables import StrategyMetadata
from shared.schemas.base import BaseSchema


class RuntimeDecision(BaseSchema):
    action: str
    direction: str
    strength: float
    target_position_ratio: float
    reason: str
    risk_tags: list[str]


@dataclass(slots=True)
class StrategyRuntimeContext:
    strategy: StrategyMetadata
    analysis: AnalysisAgentOutput
    selection: StrategySelectionOutput
    snapshot: MarketFeatureSnapshot
    account_state: dict[str, Any]
    current_position: dict[str, Any]
    current_side: str
    current_ratio: float
    max_ratio: float


class BaseStrategyRuntime(ABC):
    strategy_ids: tuple[str, ...] = ()
    strategy_types: tuple[str, ...] = ()

    def supports(self, strategy: StrategyMetadata) -> bool:
        return strategy.strategy_id in self.strategy_ids or strategy.strategy_type in self.strategy_types

    @abstractmethod
    def get_signal(self, context: StrategyRuntimeContext) -> RuntimeDecision:
        raise NotImplementedError
