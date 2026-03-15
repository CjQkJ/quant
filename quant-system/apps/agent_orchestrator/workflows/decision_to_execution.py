"""审核到执行的工作流。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from apps.agent_orchestrator.agents.executor_agent import ExecutorAgent
from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from apps.execution_engine.schemas.execution import ExecutionResultOutput
from apps.risk_engine.schemas.risk import AuditDecisionOutput
from shared.models.tables import MarketOrderBookSnapshot


class DecisionToExecutionWorkflow:
    def __init__(self, executor_agent: ExecutorAgent) -> None:
        self.executor_agent = executor_agent

    def run(
        self,
        session: Session,
        analysis: AnalysisAgentOutput,
        audit: AuditDecisionOutput,
        orderbook: MarketOrderBookSnapshot,
    ) -> ExecutionResultOutput:
        return self.executor_agent.run(session, analysis=analysis, audit=audit, orderbook=orderbook)

