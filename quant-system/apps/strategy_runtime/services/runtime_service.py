"""策略运行时信号服务。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from apps.market_data.services.regime_feature_service import RegimeFeatureService
from apps.strategy_registry.schemas.strategy import StrategySelectionOutput
from apps.strategy_registry.services.registry_service import RegistryService
from apps.strategy_runtime.schemas.signal import StrategySignal
from shared.constants.versions import STRATEGY_RUNTIME_VERSION
from shared.models.enums import SignalAction
from shared.models.tables import StrategySignalRecord
from shared.utils.ids import new_signal_id
from shared.utils.time import utc_now


class StrategyRuntimeService:
    """根据已选策略生成运行时信号。"""

    version = STRATEGY_RUNTIME_VERSION

    def __init__(self, account_state_service) -> None:
        self.account_state_service = account_state_service
        self.feature_service = RegimeFeatureService()
        self.registry = RegistryService()

    def get_strategy_signal(
        self,
        session: Session,
        analysis: AnalysisAgentOutput,
        selection: StrategySelectionOutput,
    ) -> StrategySignal:
        strategy = self.registry.get_by_strategy_id(session, selection.selected_strategy_id)
        if strategy is None:
            raise ValueError(f"未找到策略 {selection.selected_strategy_id}")

        snapshot = self.feature_service.build_snapshot(session, symbol=analysis.symbol, timeframe=analysis.timeframe)
        account = self.account_state_service.get()
        position = account.get("positions", {}).get(
            analysis.symbol,
            {
                "qty": 0.0,
                "side": "flat",
                "notional": 0.0,
            },
        )
        current_side = position.get("side", "flat")
        equity = float(account.get("equity", 0.0)) or 1.0
        current_ratio = abs(float(position.get("notional", 0.0))) / equity
        max_ratio = float(strategy.max_position_ratio)

        action = SignalAction.NO_TRADE
        direction = "flat"
        strength = round(max(analysis.confidence, 0.05), 4)
        target_ratio = 0.0
        reason = "未触发策略条件"
        risk_tags = list(analysis.risk_flags)

        if strategy.strategy_type == "defensive":
            action = SignalAction.NO_TRADE
            direction = current_side if current_side != "flat" else "flat"
            reason = "防御型策略默认不触发交易"
        elif strategy.strategy_type == "mean_reversion":
            desired_direction = "short" if "short" in analysis.directional_bias else "long" if "long" in analysis.directional_bias else "flat"
            if analysis.market_regime != "range":
                action = SignalAction.NO_TRADE
                direction = desired_direction
                reason = "均值回归策略仅在震荡市场启用"
            elif current_side != "flat" and current_side != desired_direction and desired_direction != "flat":
                action = SignalAction.EXIT
                direction = current_side
                reason = "均值回归方向反转，先退出原方向仓位"
            elif desired_direction == "flat":
                action = SignalAction.HOLD if current_side != "flat" else SignalAction.NO_TRADE
                direction = current_side
                reason = "方向中性，保持或不交易"
            elif current_side == desired_direction and current_ratio > max_ratio * 0.7:
                action = SignalAction.REDUCE
                direction = current_side
                target_ratio = round(max_ratio * 0.5, 4)
                reason = "均值回归已有仓位，先减仓控制暴露"
            else:
                action = SignalAction.ENTRY
                direction = desired_direction
                target_ratio = round(max_ratio, 4)
                reason = "均值回归策略触发入场"
        elif strategy.strategy_type == "trend_following":
            if analysis.directional_bias in {"long", "neutral_to_long"} and analysis.market_regime in {"trend", "high_vol"}:
                if current_side == "short":
                    action = SignalAction.EXIT
                    direction = "short"
                    reason = "趋势策略不持有反向空头仓位"
                elif current_ratio >= max_ratio * 0.8:
                    action = SignalAction.HOLD
                    direction = "long"
                    reason = "趋势多头仓位已接近目标"
                else:
                    action = SignalAction.ENTRY
                    direction = "long"
                    target_ratio = round(max_ratio, 4)
                    reason = "趋势策略触发做多"
            elif current_side == "long":
                action = SignalAction.REDUCE if analysis.confidence >= 0.45 else SignalAction.EXIT
                direction = "long"
                target_ratio = round(max_ratio * 0.4, 4) if action == SignalAction.REDUCE else 0.0
                reason = "趋势条件转弱，降低或退出多头暴露"
            else:
                action = SignalAction.NO_TRADE
                direction = "flat"
                reason = "趋势策略当前无有效入场信号"
        else:
            action = SignalAction.NO_TRADE
            direction = current_side
            reason = "当前策略类型未接入运行时"

        if snapshot.spread_bps > 10:
            risk_tags.append("wide_spread_runtime")

        output = StrategySignal(
            signal_id=new_signal_id(),
            task_id=analysis.task_id,
            analysis_id=analysis.analysis_id,
            selection_id=selection.selection_id,
            strategy_id=selection.selected_strategy_id,
            symbol=analysis.symbol,
            timeframe=analysis.timeframe,
            market_type="futures",
            signal_time=utc_now(),
            action=action,
            direction=direction,
            strength=strength,
            target_position_ratio=target_ratio,
            reason=reason,
            risk_tags=sorted(set(risk_tags)),
            strategy_runtime_version=self.version,
        )
        row = StrategySignalRecord(
            signal_id=output.signal_id,
            task_id=output.task_id,
            analysis_id=output.analysis_id,
            selection_id=output.selection_id,
            strategy_id=output.strategy_id,
            symbol=output.symbol,
            timeframe=output.timeframe,
            market_type=output.market_type,
            action=output.action,
            direction=output.direction,
            strength=output.strength,
            target_position_ratio=output.target_position_ratio,
            reason=output.reason,
            risk_tags=output.risk_tags,
            strategy_runtime_version=output.strategy_runtime_version,
            raw_payload=output.model_dump(mode="json"),
        )
        session.add(row)
        session.flush()
        return output
