"""趋势做多运行时。"""

from __future__ import annotations

from apps.strategy_runtime.base import BaseStrategyRuntime, RuntimeDecision, StrategyRuntimeContext
from shared.models.enums import SignalAction


class TrendLongRuntime(BaseStrategyRuntime):
    strategy_ids = ("trend_long_btc_5m_v1",)
    strategy_types = ("trend_following",)

    def get_signal(self, context: StrategyRuntimeContext) -> RuntimeDecision:
        action = SignalAction.NO_TRADE
        direction = "flat"
        target_ratio = 0.0
        reason = "趋势策略当前没有有效入场"

        if context.analysis.directional_bias in {"long", "neutral_to_long"} and context.analysis.market_regime in {"trend", "high_vol"}:
            if context.current_side == "short":
                action = SignalAction.EXIT
                direction = "short"
                reason = "趋势做多策略先退出反向空头仓位"
            elif context.current_ratio >= context.max_ratio * 0.8:
                action = SignalAction.HOLD
                direction = "long"
                reason = "已有多头仓位接近目标，保持持仓"
            else:
                action = SignalAction.ENTRY
                direction = "long"
                target_ratio = round(context.max_ratio, 4)
                reason = "趋势做多条件触发入场"
        elif context.current_side == "long":
            action = SignalAction.REDUCE if context.analysis.confidence >= 0.45 else SignalAction.EXIT
            direction = "long"
            target_ratio = round(context.max_ratio * 0.4, 4) if action == SignalAction.REDUCE else 0.0
            reason = "趋势条件转弱，降低或退出多头暴露"

        return RuntimeDecision(
            action=action,
            direction=direction,
            strength=round(max(context.analysis.confidence, 0.05), 4),
            target_position_ratio=target_ratio,
            reason=reason,
            risk_tags=list(context.analysis.risk_flags),
        )
