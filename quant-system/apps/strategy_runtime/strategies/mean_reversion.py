"""均值回归运行时。"""

from __future__ import annotations

from apps.strategy_runtime.base import BaseStrategyRuntime, RuntimeDecision, StrategyRuntimeContext
from shared.models.enums import SignalAction


class MeanReversionRuntime(BaseStrategyRuntime):
    strategy_ids = ("mr_btc_5m_v1",)
    strategy_types = ("mean_reversion",)

    def get_signal(self, context: StrategyRuntimeContext) -> RuntimeDecision:
        desired_direction = (
            "short"
            if "short" in context.analysis.directional_bias
            else "long"
            if "long" in context.analysis.directional_bias
            else "flat"
        )
        action = SignalAction.NO_TRADE
        direction = desired_direction
        target_ratio = 0.0
        reason = "均值回归条件未满足"

        if context.analysis.market_regime != "range":
            reason = "均值回归策略仅在震荡行情启用"
        elif context.current_side != "flat" and context.current_side != desired_direction and desired_direction != "flat":
            action = SignalAction.EXIT
            direction = context.current_side
            reason = "方向反转，先退出原持仓"
        elif desired_direction == "flat":
            action = SignalAction.HOLD if context.current_side != "flat" else SignalAction.NO_TRADE
            direction = context.current_side
            reason = "当前无明确方向，保持观望"
        elif context.current_side == desired_direction and context.current_ratio > context.max_ratio * 0.7:
            action = SignalAction.REDUCE
            direction = context.current_side
            target_ratio = round(context.max_ratio * 0.5, 4)
            reason = "已有同向仓位，先做减仓控制"
        else:
            action = SignalAction.ENTRY
            direction = desired_direction
            target_ratio = round(context.max_ratio, 4)
            reason = "均值回归条件触发入场"

        return RuntimeDecision(
            action=action,
            direction=direction,
            strength=round(max(context.analysis.confidence, 0.05), 4),
            target_position_ratio=target_ratio,
            reason=reason,
            risk_tags=list(context.analysis.risk_flags),
        )
