"""策略运行时信号服务。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from apps.market_data.services.regime_feature_service import RegimeFeatureService
from apps.strategy_registry.schemas.strategy import StrategySelectionOutput
from apps.strategy_registry.services.registry_service import RegistryService
from apps.strategy_runtime.base import StrategyRuntimeContext
from apps.strategy_runtime.registry import StrategyRuntimeRegistry
from apps.strategy_runtime.schemas.signal import StrategySignal
from shared.constants.versions import STRATEGY_RUNTIME_VERSION
from shared.models.tables import StrategySignalRecord
from shared.utils.ids import new_signal_id
from shared.utils.time import utc_now


class StrategyRuntimeService:
    """按 strategy_id 路由运行时实现，并持久化策略信号。"""

    version = STRATEGY_RUNTIME_VERSION

    def __init__(self, account_state_service) -> None:
        self.account_state_service = account_state_service
        self.feature_service = RegimeFeatureService()
        self.registry = RegistryService()
        self.runtime_registry = StrategyRuntimeRegistry()

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
        position = account.get(
            "positions",
            {},
        ).get(
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

        context = StrategyRuntimeContext(
            strategy=strategy,
            analysis=analysis,
            selection=selection,
            snapshot=snapshot,
            account_state=account,
            current_position=position,
            current_side=current_side,
            current_ratio=current_ratio,
            max_ratio=max_ratio,
        )
        decision = self.runtime_registry.get_runtime(strategy).get_signal(context)

        risk_tags = list(decision.risk_tags)
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
            action=decision.action,
            direction=decision.direction,
            strength=decision.strength,
            target_position_ratio=decision.target_position_ratio,
            reason=decision.reason,
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
