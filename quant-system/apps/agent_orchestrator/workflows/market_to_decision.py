"""市场到审核的工作流。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from apps.agent_orchestrator.agents.analyst_agent import AnalystAgent
from apps.agent_orchestrator.agents.auditor_agent import AuditorAgent
from apps.agent_orchestrator.agents.selector_agent import SelectorAgent
from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from apps.risk_engine.schemas.risk import AuditDecisionOutput
from apps.strategy_registry.schemas.strategy import StrategySelectionOutput
from apps.strategy_runtime.schemas.signal import StrategySignal
from apps.strategy_runtime.services.runtime_service import StrategyRuntimeService


class MarketToDecisionWorkflow:
    def __init__(
        self,
        analyst_agent: AnalystAgent,
        selector_agent: SelectorAgent,
        auditor_agent: AuditorAgent,
        strategy_runtime_service: StrategyRuntimeService,
    ) -> None:
        self.analyst_agent = analyst_agent
        self.selector_agent = selector_agent
        self.auditor_agent = auditor_agent
        self.strategy_runtime_service = strategy_runtime_service

    def run(
        self,
        session: Session,
        task_id: str,
        symbol: str,
        timeframe: str = "5m",
    ) -> tuple[AnalysisAgentOutput, StrategySelectionOutput, StrategySignal, AuditDecisionOutput]:
        analysis = self.analyst_agent.run(session, task_id=task_id, symbol=symbol, timeframe=timeframe)
        selection = self.selector_agent.run(session, analysis=analysis)
        strategy_signal = self.strategy_runtime_service.get_strategy_signal(session, analysis=analysis, selection=selection)
        audit = self.auditor_agent.run(session, analysis=analysis, selection=selection, strategy_signal=strategy_signal)
        return analysis, selection, strategy_signal, audit
