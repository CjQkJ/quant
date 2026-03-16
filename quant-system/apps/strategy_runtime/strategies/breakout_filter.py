"""突破过滤运行时。"""

from __future__ import annotations

from apps.strategy_runtime.base import BaseStrategyRuntime, RuntimeDecision, StrategyRuntimeContext
from shared.models.enums import SignalAction


class BreakoutFilterRuntime(BaseStrategyRuntime):
    strategy_ids = ("breakout_filter_btc_5m_v1",)
    strategy_types = ("breakout_filter",)

    def get_signal(self, context: StrategyRuntimeContext) -> RuntimeDecision:
        if context.analysis.market_regime in {"event", "high_vol"} and context.analysis.directional_bias in {"long", "neutral_to_long"}:
            return RuntimeDecision(
                action=SignalAction.ENTRY,
                direction="long",
                strength=round(max(context.analysis.confidence, 0.05), 4),
                target_position_ratio=round(min(context.max_ratio, 0.08), 4),
                reason="突破过滤策略在事件/高波动上行阶段允许轻仓跟随",
                risk_tags=list(context.analysis.risk_flags),
            )
        if context.analysis.market_regime in {"event", "high_vol"} and context.analysis.directional_bias in {"short", "neutral_to_short"}:
            return RuntimeDecision(
                action=SignalAction.ENTRY,
                direction="short",
                strength=round(max(context.analysis.confidence, 0.05), 4),
                target_position_ratio=round(min(context.max_ratio, 0.08), 4),
                reason="突破过滤策略在事件/高波动下行阶段允许轻仓跟随",
                risk_tags=list(context.analysis.risk_flags),
            )
        if context.current_side != "flat":
            return RuntimeDecision(
                action=SignalAction.REDUCE,
                direction=context.current_side,
                strength=round(max(context.analysis.confidence, 0.05), 4),
                target_position_ratio=round(context.max_ratio * 0.3, 4),
                reason="突破条件消失，降低已有仓位",
                risk_tags=list(context.analysis.risk_flags),
            )
        return RuntimeDecision(
            action=SignalAction.NO_TRADE,
            direction="flat",
            strength=round(max(context.analysis.confidence, 0.05), 4),
            target_position_ratio=0.0,
            reason="突破过滤条件未满足",
            risk_tags=list(context.analysis.risk_flags),
        )
