"""回放结果评估器。"""

from __future__ import annotations

from collections import Counter

from apps.agent_orchestrator.schemas.orchestration import CycleResultOutput, ReplayRunSummary, VersionMatrix


class ReplayEvaluator:
    def evaluate(
        self,
        *,
        run_id: str,
        symbol: str,
        timeframe: str,
        fixture_name: str,
        version_matrix: VersionMatrix,
        cycle_results: list[CycleResultOutput],
    ) -> ReplayRunSummary:
        if not cycle_results:
            raise ValueError("回放结果为空，无法生成 summary")

        selected_strategy_counter: Counter[str] = Counter()
        decision_counter: Counter[str] = Counter()
        switch_count = 0
        switch_attempt_count = 0
        cooldown_block_count = 0
        execution_success_count = 0
        last_selected_strategy_id: str | None = None

        for result in cycle_results:
            selected_strategy_counter[result.selection.selected_strategy_id] += 1
            decision_counter[result.audit.decision] += 1
            if result.execution.execution_status == "filled":
                execution_success_count += 1
            if result.selection.switch_attempted:
                switch_attempt_count += 1
            if result.selection.cooldown_applied:
                cooldown_block_count += 1
            if last_selected_strategy_id and last_selected_strategy_id != result.selection.selected_strategy_id:
                switch_count += 1
            last_selected_strategy_id = result.selection.selected_strategy_id

        final_snapshot = cycle_results[-1].account_snapshot
        return ReplayRunSummary(
            run_id=run_id,
            symbol=symbol,
            timeframe=timeframe,
            fixture_name=fixture_name,
            version_matrix=version_matrix,
            analysis_version=version_matrix.analysis_version,
            ranking_version=version_matrix.ranking_version,
            risk_policy_version=version_matrix.risk_policy_version,
            strategy_runtime_version=version_matrix.strategy_runtime_version,
            cycle_count=len(cycle_results),
            strategy_switch_count=switch_count,
            strategy_switch_attempt_count=switch_attempt_count,
            cooldown_block_count=cooldown_block_count,
            execution_success_ratio=round(execution_success_count / len(cycle_results), 4),
            decision_breakdown=dict(decision_counter),
            selected_strategy_breakdown=dict(selected_strategy_counter),
            final_equity=final_snapshot.equity,
            final_cash_balance=final_snapshot.cash_balance,
            final_realized_pnl=final_snapshot.realized_pnl,
            final_unrealized_pnl=final_snapshot.unrealized_pnl,
            total_fee_paid=final_snapshot.fee_paid_total,
            avg_slippage_bps=final_snapshot.avg_slippage_bps,
            account_snapshot=final_snapshot,
            cycle_results=cycle_results,
        )
