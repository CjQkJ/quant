"""历史回放驱动。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from apps.agent_orchestrator.replay.replay_evaluator import ReplayEvaluator
from apps.agent_orchestrator.schemas.orchestration import ReplayRunSummary, VersionMatrix
from apps.market_data.schemas.market import OHLCVPayload
from apps.market_data.services.ohlcv_service import OHLCVService
from shared.config.risk_policy import get_risk_policy
from shared.constants.versions import ANALYSIS_VERSION, RANKING_VERSION, STRATEGY_RUNTIME_VERSION
from shared.models.tables import ReplayCycleResult, ReplayRun
from shared.utils.ids import new_replay_cycle_id, new_replay_run_id
from shared.utils.time import utc_now


class ReplayRunner:
    def __init__(self, orchestrator) -> None:
        self.orchestrator = orchestrator
        self.ohlcv_service = OHLCVService()
        self.evaluator = ReplayEvaluator()

    def run(
        self,
        session: Session,
        bars: list[dict],
        symbol: str,
        timeframe: str = "5m",
        fixture_name: str = "replay_bars.json",
    ) -> ReplayRunSummary:
        policy = get_risk_policy()
        run_id = new_replay_run_id()
        version_matrix = VersionMatrix(
            analysis_version=ANALYSIS_VERSION,
            ranking_version=RANKING_VERSION,
            risk_policy_version=policy.version,
            strategy_runtime_version=STRATEGY_RUNTIME_VERSION,
        )
        run_row = ReplayRun(
            run_id=run_id,
            symbol=symbol,
            timeframe=timeframe,
            fixture_name=fixture_name,
            analysis_version=version_matrix.analysis_version,
            ranking_version=version_matrix.ranking_version,
            risk_policy_version=version_matrix.risk_policy_version,
            strategy_runtime_version=version_matrix.strategy_runtime_version,
            started_at=utc_now(),
            completed_at=None,
            summary_json=None,
        )
        session.add(run_row)
        session.flush()

        results = []

        for index, bar in enumerate(bars):
            payload = OHLCVPayload.model_validate(bar)
            self.ohlcv_service.save_many(session, [payload])
            session.commit()
            result = self.orchestrator.run_cycle(session, symbol=symbol, timeframe=timeframe)
            session.commit()
            results.append(result)

            session.add(
                ReplayCycleResult(
                    cycle_id=new_replay_cycle_id(),
                    run_id=run_id,
                    task_id=result.task_id,
                    cycle_index=index,
                    bar_time=payload.close_time,
                    selected_strategy_id=result.selection.selected_strategy_id,
                    strategy_signal_action=result.strategy_signal.action,
                    strategy_signal_direction=result.strategy_signal.direction,
                    audit_decision=result.audit.decision,
                    execution_status=result.execution.execution_status,
                    switch_attempted=result.selection.switch_attempted,
                    cooldown_applied=result.selection.cooldown_applied,
                    account_snapshot_json=result.account_snapshot.model_dump(mode="json"),
                    raw_payload=result.model_dump(mode="json"),
                )
            )
            session.flush()

        summary = self.evaluator.evaluate(
            run_id=run_id,
            symbol=symbol,
            timeframe=timeframe,
            fixture_name=fixture_name,
            version_matrix=version_matrix,
            cycle_results=results,
        )
        run_row.completed_at = utc_now()
        run_row.summary_json = summary.model_dump(mode="json")
        session.flush()
        return summary
