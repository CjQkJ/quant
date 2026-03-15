"""编排结果结构。"""

from __future__ import annotations

from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from apps.execution_engine.schemas.execution import ExecutionResultOutput
from apps.risk_engine.schemas.risk import AuditDecisionOutput, MonitorStatusOutput
from apps.strategy_registry.schemas.strategy import StrategySelectionOutput
from shared.schemas.base import BaseSchema


class CycleResultOutput(BaseSchema):
    task_id: str
    analysis: AnalysisAgentOutput
    selection: StrategySelectionOutput
    audit: AuditDecisionOutput
    execution: ExecutionResultOutput
    monitor: MonitorStatusOutput

