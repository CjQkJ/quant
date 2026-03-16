"""防御观察运行时。"""

from __future__ import annotations

from apps.strategy_runtime.base import BaseStrategyRuntime, RuntimeDecision, StrategyRuntimeContext
from shared.models.enums import SignalAction


class DefensiveNoTradeRuntime(BaseStrategyRuntime):
    strategy_ids = ("defensive_no_trade_btc_5m_v1",)
    strategy_types = ("defensive",)

    def get_signal(self, context: StrategyRuntimeContext) -> RuntimeDecision:
        direction = context.current_side if context.current_side != "flat" else "flat"
        return RuntimeDecision(
            action=SignalAction.NO_TRADE,
            direction=direction,
            strength=round(max(context.analysis.confidence, 0.05), 4),
            target_position_ratio=0.0,
            reason="防御观察策略默认不触发交易",
            risk_tags=list(context.analysis.risk_flags),
        )
