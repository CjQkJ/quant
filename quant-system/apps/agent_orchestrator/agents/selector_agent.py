"""策略选择智能体。"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from apps.strategy_registry.schemas.strategy import StrategySelectionOutput
from apps.strategy_registry.services.ranking_service import RankingService
from apps.strategy_registry.services.registry_service import RegistryService
from apps.strategy_registry.services.selection_policy_service import SelectionPolicyService
from apps.strategy_registry.services.strategy_matcher import StrategyMatcher
from shared.models.tables import StrategySelection
from shared.utils.state_store import InMemoryStateStore, StateStore
from shared.utils.ids import new_selection_id
from shared.utils.time import utc_now


class SelectorAgent:
    def __init__(self, state_store: StateStore | None = None) -> None:
        self.registry = RegistryService()
        self.matcher = StrategyMatcher()
        self.ranker = RankingService()
        self.state_store = state_store or InMemoryStateStore()
        self.policy_service = SelectionPolicyService(self.state_store)

    def run(self, session: Session, analysis: AnalysisAgentOutput) -> StrategySelectionOutput:
        available = self.registry.list_enabled(session, symbol=analysis.symbol, timeframe=analysis.timeframe)
        matched = self.matcher.match(available, analysis)
        if not matched:
            matched = available
        ranked = self.ranker.rank(matched, analysis)
        if not ranked:
            raise ValueError("策略库为空，无法完成策略选择")
        primary, switch_attempted, cooldown_applied, note = self.policy_service.apply(
            symbol=analysis.symbol,
            timeframe=analysis.timeframe,
            ranked=ranked,
        )
        if self.registry.get_by_strategy_id(session, primary.strategy_id) is None:
            raise ValueError(f"策略 {primary.strategy_id} 不存在，无法完成策略选择")
        fallback = ranked[1].strategy_id if len(ranked) > 1 else None
        output = StrategySelectionOutput(
            task_id=analysis.task_id,
            analysis_id=analysis.analysis_id,
            selection_id=new_selection_id(),
            selection_time=utc_now().isoformat(),
            ranking_version=self.ranker.version,
            selected_strategy_id=primary.strategy_id,
            selected_strategy_name=primary.strategy_name,
            selected_strategy_type=primary.strategy_type,
            fit_score=primary.fit_score,
            candidate_strategies=ranked,
            fallback_strategy_id=fallback,
            selection_reason=primary.reason,
            constraints_checked=[
                "symbol_supported",
                "timeframe_supported",
                "market_regime_fit",
                "directional_fit",
            ],
            switch_attempted=switch_attempted,
            cooldown_applied=cooldown_applied,
            selection_policy_note=note,
        )
        row = StrategySelection(
            selection_id=output.selection_id,
            task_id=output.task_id,
            analysis_id=output.analysis_id,
            ranking_version=output.ranking_version,
            selected_strategy_id=output.selected_strategy_id,
            selected_strategy_name=output.selected_strategy_name,
            selected_strategy_type=output.selected_strategy_type,
            candidate_strategies=[candidate.model_dump() for candidate in output.candidate_strategies],
            selection_reason=output.selection_reason,
            fit_score=Decimal(str(output.fit_score)),
            fallback_strategy_id=output.fallback_strategy_id,
            switch_attempted=output.switch_attempted,
            cooldown_applied=output.cooldown_applied,
            selection_policy_note=output.selection_policy_note,
            raw_payload=output.model_dump(mode="json"),
            created_by_agent="selector_agent",
        )
        session.add(row)
        session.flush()
        return output
