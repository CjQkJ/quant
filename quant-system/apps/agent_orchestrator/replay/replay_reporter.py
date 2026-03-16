"""回放结果报告器。"""

from __future__ import annotations

from apps.agent_orchestrator.schemas.orchestration import ReplayRunSummary


class ReplayReporter:
    def to_console_lines(self, summary: ReplayRunSummary) -> list[str]:
        return [
            f"回放完成，共 {summary.cycle_count} 个 bar",
            "版本矩阵: "
            f"{summary.version_matrix.analysis_version} / "
            f"{summary.version_matrix.ranking_version} / "
            f"{summary.version_matrix.risk_policy_version} / "
            f"{summary.version_matrix.strategy_runtime_version}",
            f"策略切换次数: {summary.strategy_switch_count}",
            f"策略切换尝试次数: {summary.strategy_switch_attempt_count}",
            f"冷却阻止次数: {summary.cooldown_block_count}",
            f"执行成功率: {summary.execution_success_ratio:.2%}",
            f"最终权益: {summary.final_equity:.2f}",
            f"累计手续费: {summary.total_fee_paid:.2f}",
            f"平均滑点: {summary.avg_slippage_bps:.2f} bps",
        ]

    def to_markdown(self, summary: ReplayRunSummary) -> str:
        return "\n".join(
            [
                "# Replay Summary",
                "",
                f"- run_id: `{summary.run_id}`",
                f"- symbol: `{summary.symbol}`",
                f"- timeframe: `{summary.timeframe}`",
                f"- fixture: `{summary.fixture_name}`",
                f"- version_matrix: `{summary.version_matrix.analysis_version} / {summary.version_matrix.ranking_version} / {summary.version_matrix.risk_policy_version} / {summary.version_matrix.strategy_runtime_version}`",
                f"- cycle_count: `{summary.cycle_count}`",
                f"- strategy_switch_count: `{summary.strategy_switch_count}`",
                f"- strategy_switch_attempt_count: `{summary.strategy_switch_attempt_count}`",
                f"- cooldown_block_count: `{summary.cooldown_block_count}`",
                f"- execution_success_ratio: `{summary.execution_success_ratio:.2%}`",
                f"- final_equity: `{summary.final_equity:.2f}`",
                f"- final_cash_balance: `{summary.final_cash_balance:.2f}`",
                f"- final_realized_pnl: `{summary.final_realized_pnl:.2f}`",
                f"- final_unrealized_pnl: `{summary.final_unrealized_pnl:.2f}`",
                f"- total_fee_paid: `{summary.total_fee_paid:.2f}`",
                f"- avg_slippage_bps: `{summary.avg_slippage_bps:.2f}`",
            ]
        )
