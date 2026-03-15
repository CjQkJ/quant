"""市场到审核的工作流。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from apps.agent_orchestrator.agents.analyst_agent import AnalystAgent
from apps.agent_orchestrator.agents.auditor_agent import AuditorAgent
from apps.agent_orchestrator.agents.selector_agent import SelectorAgent
from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from apps.risk_engine.schemas.risk import AuditDecisionOutput
from apps.strategy_registry.schemas.strategy import StrategySelectionOutput


class MarketToDecisionWorkflow:
    def __init__(
        self,
        analyst_agent: AnalystAgent,
        selector_agent: SelectorAgent,
        auditor_agent: AuditorAgent,
    ) -> None:
        self.analyst_agent = analyst_agent
        self.selector_agent = selector_agent
        self.auditor_agent = auditor_agent

    def run(
        self,
        session: Session,
        task_id: str,
        symbol: str,
        timeframe: str = "5m",
    ) -> tuple[AnalysisAgentOutput, StrategySelectionOutput, AuditDecisionOutput]:
        analysis = self.analyst_agent.run(session, task_id=task_id, symbol=symbol, timeframe=timeframe)
        selection = self.selector_agent.run(session, analysis=analysis)
        audit = self.auditor_agent.run(session, analysis=analysis, selection=selection)
        return analysis, selection, audit

