"""执行智能体。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from apps.execution_engine.schemas.execution import ExecutionResultOutput
from apps.execution_engine.services.order_executor import OrderExecutor
from apps.execution_engine.services.order_planner import OrderPlanner
from apps.risk_engine.schemas.risk import AuditDecisionOutput
from shared.models.tables import MarketOrderBookSnapshot


class ExecutorAgent:
    def __init__(self, planner: OrderPlanner, executor: OrderExecutor) -> None:
        self.planner = planner
        self.executor = executor

    def run(
        self,
        session: Session,
        analysis: AnalysisAgentOutput,
        audit: AuditDecisionOutput,
        orderbook: MarketOrderBookSnapshot,
    ) -> ExecutionResultOutput:
        planned = self.planner.plan(session, analysis=analysis, audit=audit, orderbook=orderbook)
        return self.executor.execute(
            session,
            task_id=analysis.task_id,
            audit=audit,
            planned_orders=planned,
            best_bid=float(orderbook.best_bid),
            best_ask=float(orderbook.best_ask),
        )

