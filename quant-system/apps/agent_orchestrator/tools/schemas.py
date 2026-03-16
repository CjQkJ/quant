"""工具执行层输入输出结构。"""

from __future__ import annotations

from typing import Any

from apps.agent_orchestrator.schemas.orchestration import CycleResultOutput, ReplayRunSummary
from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from apps.execution_engine.schemas.execution import PaperAccountSnapshot
from apps.market_data.schemas.feature import MarketFeatureSnapshot
from apps.risk_engine.schemas.risk import AuditDecisionOutput, MonitorStatusOutput
from apps.strategy_registry.schemas.strategy import StrategySelectionOutput
from apps.strategy_runtime.schemas.signal import StrategySignal
from pydantic import Field

from shared.schemas.base import BaseSchema


class ToolExecutionEnvelope(BaseSchema):
    task_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class ToolCatalogItem(BaseSchema):
    name: str
    description: str
    risk_level: str
    roles: list[str]
    input_schema: str
    output_schema: str


class SymbolTimeframeInput(BaseSchema):
    symbol: str = "BTCUSDT"
    timeframe: str = "5m"


class SymbolOnlyInput(BaseSchema):
    symbol: str = "BTCUSDT"


class ReplayScenarioInput(BaseSchema):
    fixture_name: str = "replay_bars.json"
    symbol: str = "BTCUSDT"
    timeframe: str = "5m"


class AccountSnapshotOutput(BaseSchema):
    account_snapshot: PaperAccountSnapshot


class MarketContextOutput(BaseSchema):
    market_context: MarketFeatureSnapshot


class LatestAnalysisOutput(BaseSchema):
    analysis: AnalysisAgentOutput | None = None


class StrategyCandidatesOutput(BaseSchema):
    selection: StrategySelectionOutput | None = None


class StrategySignalOutput(BaseSchema):
    strategy_signal: StrategySignal | None = None


class PreviewAuditDecisionOutput(BaseSchema):
    audit: AuditDecisionOutput


class RunPaperCycleOutput(BaseSchema):
    cycle_result: CycleResultOutput


class MonitorStatusToolOutput(BaseSchema):
    monitor_status: MonitorStatusOutput


class ReplayScenarioOutput(BaseSchema):
    replay_summary: ReplayRunSummary
