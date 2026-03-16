"""策略运行时注册表。"""

from __future__ import annotations

from apps.strategy_runtime.base import BaseStrategyRuntime
from apps.strategy_runtime.strategies.breakout_filter import BreakoutFilterRuntime
from apps.strategy_runtime.strategies.defensive import DefensiveNoTradeRuntime
from apps.strategy_runtime.strategies.mean_reversion import MeanReversionRuntime
from apps.strategy_runtime.strategies.trend_long import TrendLongRuntime
from shared.models.tables import StrategyMetadata


class StrategyRuntimeRegistry:
    def __init__(self) -> None:
        self._runtimes: list[BaseStrategyRuntime] = [
            MeanReversionRuntime(),
            TrendLongRuntime(),
            DefensiveNoTradeRuntime(),
            BreakoutFilterRuntime(),
        ]

    def get_runtime(self, strategy: StrategyMetadata) -> BaseStrategyRuntime:
        for runtime in self._runtimes:
            if runtime.supports(strategy):
                return runtime
        raise ValueError(f"策略 {strategy.strategy_id} 尚未注册运行时实现")
