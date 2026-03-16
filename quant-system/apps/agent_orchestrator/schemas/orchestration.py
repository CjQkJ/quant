"""编排结果结构。"""

from __future__ import annotations

from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from apps.execution_engine.schemas.execution import ExecutionResultOutput, PaperAccountSnapshot
from apps.risk_engine.schemas.risk import AuditDecisionOutput, MonitorStatusOutput
from apps.strategy_registry.schemas.strategy import StrategySelectionOutput
from apps.strategy_runtime.schemas.signal import StrategySignal
from shared.schemas.base import BaseSchema


class CycleResultOutput(BaseSchema):
    task_id: str
    analysis_version: str
    ranking_version: str
    risk_policy_version: str
    strategy_runtime_version: str
    analysis: AnalysisAgentOutput
    selection: StrategySelectionOutput
    strategy_signal: StrategySignal
    audit: AuditDecisionOutput
    execution: ExecutionResultOutput
    monitor: MonitorStatusOutput
    account_snapshot: PaperAccountSnapshot


class ReplayRunSummary(BaseSchema):
    run_id: str
    symbol: str
    timeframe: str
    fixture_name: str
    analysis_version: str
    ranking_version: str
    risk_policy_version: str
    strategy_runtime_version: str
    cycle_count: int
    strategy_switch_count: int
    strategy_switch_attempt_count: int
    cooldown_block_count: int
    execution_success_ratio: float
    decision_breakdown: dict[str, int]
    selected_strategy_breakdown: dict[str, int]
    account_snapshot: PaperAccountSnapshot
    cycle_results: list[CycleResultOutput]
