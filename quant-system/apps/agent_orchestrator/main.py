"""本地 orchestrator 与 API。"""

from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.agent_orchestrator.agents.analyst_agent import AnalystAgent
from apps.agent_orchestrator.agents.auditor_agent import AuditorAgent
from apps.agent_orchestrator.agents.executor_agent import ExecutorAgent
from apps.agent_orchestrator.agents.monitor_agent import MonitorAgent
from apps.agent_orchestrator.agents.selector_agent import SelectorAgent
from apps.agent_orchestrator.schemas.orchestration import CycleResultOutput
from apps.agent_orchestrator.workflows.decision_to_execution import DecisionToExecutionWorkflow
from apps.agent_orchestrator.workflows.market_to_decision import MarketToDecisionWorkflow
from apps.execution_engine.services.account_state_service import AccountStateService
from apps.execution_engine.services.order_executor import OrderExecutor
from apps.execution_engine.services.order_planner import OrderPlanner
from apps.risk_engine.services.audit_service import AuditService
from apps.risk_engine.services.exposure_service import ExposureService
from apps.risk_engine.services.global_risk_service import GlobalRiskService
from apps.risk_engine.services.kill_switch_service import KillSwitchService
from apps.risk_engine.services.monitor_service import MonitorService
from apps.risk_engine.services.strategy_applicability_service import StrategyApplicabilityService
from shared.config.settings import get_settings
from shared.db.session import session_scope
from shared.models.tables import MarketOrderBookSnapshot, TaskEventLog
from shared.utils.ids import new_task_id
from shared.utils.state_store import InMemoryStateStore, RedisStateStore


def build_state_store():
    settings = get_settings()
    if settings.redis_url.startswith("redis://"):
        try:
            return RedisStateStore(settings.redis_url)
        except RuntimeError:
            return InMemoryStateStore()
    return InMemoryStateStore()


class OrchestratorService:
    def __init__(self, state_store=None) -> None:
        self.state_store = state_store or build_state_store()
        self.kill_switch_service = KillSwitchService(self.state_store)
        self.global_risk_service = GlobalRiskService(self.state_store)
        self.exposure_service = ExposureService(self.global_risk_service)
        self.account_state_service = AccountStateService(self.state_store)
        self.audit_service = AuditService(
            kill_switch_service=self.kill_switch_service,
            global_risk_service=self.global_risk_service,
            exposure_service=self.exposure_service,
            applicability_service=StrategyApplicabilityService(),
        )
        self.monitor_service = MonitorService(
            kill_switch_service=self.kill_switch_service,
            global_risk_service=self.global_risk_service,
            exposure_service=self.exposure_service,
        )
        self.market_to_decision = MarketToDecisionWorkflow(
            analyst_agent=AnalystAgent(),
            selector_agent=SelectorAgent(),
            auditor_agent=AuditorAgent(self.audit_service),
        )
        self.decision_to_execution = DecisionToExecutionWorkflow(
            executor_agent=ExecutorAgent(
                planner=OrderPlanner(self.account_state_service),
                executor=OrderExecutor(self.account_state_service, self.kill_switch_service),
            )
        )
        self.monitor_agent = MonitorAgent(self.monitor_service)

    def _log_event(
        self,
        session: Session,
        task_id: str,
        event_type: str,
        source: str,
        payload: dict,
        message: str,
        level: str = "info",
    ) -> None:
        session.add(
            TaskEventLog(
                task_id=task_id,
                event_type=event_type,
                event_source=source,
                event_payload=payload,
                message=message,
                level=level,
            )
        )
        session.flush()

    def run_cycle(self, session: Session, symbol: str, timeframe: str = "5m") -> CycleResultOutput:
        task_id = new_task_id()
        self._log_event(session, task_id, "market_trigger", "system", {"symbol": symbol, "timeframe": timeframe}, "市场触发")
        analysis, selection, audit = self.market_to_decision.run(session, task_id=task_id, symbol=symbol, timeframe=timeframe)
        self._log_event(session, task_id, "analysis_done", "analyst_agent", analysis.model_dump(mode="json"), "分析完成")
        self._log_event(session, task_id, "strategy_selected", "selector_agent", selection.model_dump(mode="json"), "策略选择完成")
        self._log_event(session, task_id, "audit_done", "auditor_agent", audit.model_dump(mode="json"), "审核完成")

        orderbook = session.scalar(
            select(MarketOrderBookSnapshot)
            .where(MarketOrderBookSnapshot.symbol == symbol)
            .order_by(MarketOrderBookSnapshot.snapshot_time.desc())
            .limit(1)
        )
        if orderbook is None:
            raise ValueError("缺少订单簿快照，无法执行 orchestrator")
        execution = self.decision_to_execution.run(session, analysis=analysis, audit=audit, orderbook=orderbook)
        self._log_event(session, task_id, "execution_done", "executor_agent", execution.model_dump(mode="json"), "执行阶段完成")

        monitor = self.monitor_agent.run(session, symbol=symbol)
        self._log_event(session, task_id, "monitor_done", "monitor_agent", monitor.model_dump(mode="json"), "监控阶段完成")
        return CycleResultOutput(
            task_id=task_id,
            analysis=analysis,
            selection=selection,
            audit=audit,
            execution=execution,
            monitor=monitor,
        )


app = FastAPI(title="quant-system orchestrator")
orchestrator = OrchestratorService()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/orchestrator/run-cycle")
def run_cycle(symbol: str = "BTCUSDT", timeframe: str = "5m") -> dict:
    with session_scope() as session:
        result = orchestrator.run_cycle(session, symbol=symbol, timeframe=timeframe)
        session.commit()
        return result.model_dump(mode="json")


@app.get("/risk/kill-switch")
def get_kill_switch() -> dict:
    return {"kill_switch": orchestrator.kill_switch_service.is_enabled()}


@app.post("/risk/kill-switch/{enabled}")
def set_kill_switch(enabled: bool) -> dict:
    orchestrator.kill_switch_service.set_enabled(enabled)
    return {"kill_switch": orchestrator.kill_switch_service.is_enabled()}

