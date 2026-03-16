"""本地 orchestrator 与 API。"""

from __future__ import annotations

from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.agent_orchestrator.api.dependencies import require_internal_access
from apps.agent_orchestrator.agents.analyst_agent import AnalystAgent
from apps.agent_orchestrator.agents.auditor_agent import AuditorAgent
from apps.agent_orchestrator.agents.executor_agent import ExecutorAgent
from apps.agent_orchestrator.agents.monitor_agent import MonitorAgent
from apps.agent_orchestrator.agents.output_guard import AgentOutputGuard
from apps.agent_orchestrator.agents.selector_agent import SelectorAgent
from apps.agent_orchestrator.routers.execution import router as execution_router
from apps.agent_orchestrator.routers.market_data import router as market_data_router
from apps.agent_orchestrator.routers.monitor import router as monitor_router
from apps.agent_orchestrator.routers.replay import router as replay_router
from apps.agent_orchestrator.routers.risk import router as risk_router
from apps.agent_orchestrator.routers.tools import router as tools_router
from apps.agent_orchestrator.schemas.orchestration import CycleResultOutput
from apps.agent_orchestrator.services.task_event_logger import TaskEventLogger
from apps.agent_orchestrator.workflows.decision_to_execution import DecisionToExecutionWorkflow
from apps.agent_orchestrator.workflows.market_to_decision import MarketToDecisionWorkflow
from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from apps.execution_engine.schemas.execution import ExecutionResultOutput
from apps.execution_engine.services.account_state_service import AccountStateService
from apps.execution_engine.services.order_executor import OrderExecutor
from apps.execution_engine.services.order_planner import OrderPlanner
from apps.risk_engine.schemas.risk import AuditDecisionOutput, MonitorStatusOutput
from apps.risk_engine.services.audit_service import AuditService
from apps.risk_engine.services.exposure_service import ExposureService
from apps.risk_engine.services.global_risk_service import GlobalRiskService
from apps.risk_engine.services.kill_switch_service import KillSwitchService
from apps.risk_engine.services.monitor_service import MonitorService
from apps.risk_engine.services.strategy_applicability_service import StrategyApplicabilityService
from apps.strategy_registry.schemas.strategy import StrategySelectionOutput
from apps.strategy_runtime.schemas.signal import StrategySignal
from apps.strategy_runtime.services.runtime_service import StrategyRuntimeService
from shared.config.settings import get_settings
from shared.db.session import session_scope
from shared.models.tables import MarketOrderBookSnapshot
from shared.utils.ids import new_task_id
from shared.utils.state_store import InMemoryStateStore, RedisStateStore


def build_state_store():
    settings = get_settings()
    if settings.redis_url.startswith("redis://"):
        try:
            return RedisStateStore(settings.redis_url)
        except Exception:
            return InMemoryStateStore()
    return InMemoryStateStore()


class OrchestratorService:
    def __init__(self, state_store=None) -> None:
        self.state_store = state_store or build_state_store()
        self.kill_switch_service = KillSwitchService(self.state_store)
        self.global_risk_service = GlobalRiskService(self.state_store)
        self.exposure_service = ExposureService(self.global_risk_service)
        self.account_state_service = AccountStateService(self.state_store)
        self.event_logger = TaskEventLogger()
        self.output_guard = AgentOutputGuard(self.event_logger)
        self.audit_service = AuditService(
            kill_switch_service=self.kill_switch_service,
            global_risk_service=self.global_risk_service,
            exposure_service=self.exposure_service,
            applicability_service=StrategyApplicabilityService(),
        )
        self.strategy_runtime_service = StrategyRuntimeService(self.account_state_service)
        self.monitor_service = MonitorService(
            kill_switch_service=self.kill_switch_service,
            global_risk_service=self.global_risk_service,
            exposure_service=self.exposure_service,
        )
        self.market_to_decision = MarketToDecisionWorkflow(
            analyst_agent=AnalystAgent(),
            selector_agent=SelectorAgent(self.state_store),
            auditor_agent=AuditorAgent(self.audit_service),
            strategy_runtime_service=self.strategy_runtime_service,
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
        self.event_logger.log(session, task_id, event_type, source, payload, message, level)

    def run_cycle(self, session: Session, symbol: str, timeframe: str = "5m") -> CycleResultOutput:
        task_id = new_task_id()
        self._log_event(session, task_id, "market_trigger", "system", {"symbol": symbol, "timeframe": timeframe}, "市场触发")
        analysis, selection, strategy_signal, audit = self.market_to_decision.run(session, task_id=task_id, symbol=symbol, timeframe=timeframe)
        analysis = self.output_guard.validate(session, task_id, "analyst_agent", AnalysisAgentOutput, analysis)
        selection = self.output_guard.validate(session, task_id, "selector_agent", StrategySelectionOutput, selection)
        strategy_signal = self.output_guard.validate(session, task_id, "strategy_runtime", StrategySignal, strategy_signal)
        audit = self.output_guard.validate(session, task_id, "auditor_agent", AuditDecisionOutput, audit)
        self._log_event(session, task_id, "analysis_done", "analyst_agent", analysis.model_dump(mode="json"), "分析完成")
        self._log_event(session, task_id, "strategy_selected", "selector_agent", selection.model_dump(mode="json"), "策略选择完成")
        self._log_event(session, task_id, "strategy_signal_done", "strategy_runtime", strategy_signal.model_dump(mode="json"), "策略信号生成完成")
        if audit.next_action != "none":
            self._log_event(
                session,
                task_id,
                "audit_followup_requested",
                "auditor_agent",
                {"next_action": audit.next_action, "context_requirements": audit.context_requirements},
                "审核要求补充上下文",
                level="warn",
            )
        self._log_event(session, task_id, "audit_done", "auditor_agent", audit.model_dump(mode="json"), "审核完成")

        orderbook = session.scalar(
            select(MarketOrderBookSnapshot)
            .where(MarketOrderBookSnapshot.symbol == symbol)
            .order_by(MarketOrderBookSnapshot.snapshot_time.desc())
            .limit(1)
        )
        if orderbook is None:
            raise ValueError("缺少订单簿快照，无法执行 orchestrator")
        execution = self.decision_to_execution.run(session, analysis=analysis, audit=audit, strategy_signal=strategy_signal, orderbook=orderbook)
        execution = self.output_guard.validate(session, task_id, "executor_agent", ExecutionResultOutput, execution)
        self._log_event(session, task_id, "execution_done", "executor_agent", execution.model_dump(mode="json"), "执行阶段完成")

        monitor = self.monitor_agent.run(session, symbol=symbol)
        monitor = self.output_guard.validate(session, task_id, "monitor_agent", MonitorStatusOutput, monitor)
        self._log_event(session, task_id, "monitor_done", "monitor_agent", monitor.model_dump(mode="json"), "监控阶段完成")
        return CycleResultOutput(
            task_id=task_id,
            analysis_version=analysis.analysis_version,
            ranking_version=selection.ranking_version,
            risk_policy_version=audit.risk_policy_version,
            strategy_runtime_version=strategy_signal.strategy_runtime_version,
            analysis=analysis,
            selection=selection,
            strategy_signal=strategy_signal,
            audit=audit,
            execution=execution,
            monitor=monitor,
            account_snapshot=execution.account_snapshot,
        )


app = FastAPI(title="quant-system orchestrator")
orchestrator = OrchestratorService()
app.include_router(market_data_router)
app.include_router(risk_router)
app.include_router(execution_router)
app.include_router(replay_router)
app.include_router(monitor_router)
app.include_router(tools_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/orchestrator/run-cycle", dependencies=[Depends(require_internal_access)])
def run_cycle(symbol: str = "BTCUSDT", timeframe: str = "5m") -> dict:
    with session_scope() as session:
        result = orchestrator.run_cycle(session, symbol=symbol, timeframe=timeframe)
        session.commit()
        return result.model_dump(mode="json")


@app.get("/risk/kill-switch", dependencies=[Depends(require_internal_access)])
def get_kill_switch() -> dict:
    return {"kill_switch": orchestrator.kill_switch_service.is_enabled()}


@app.post("/risk/kill-switch/{enabled}", dependencies=[Depends(require_internal_access)])
def set_kill_switch(enabled: bool) -> dict:
    orchestrator.kill_switch_service.set_enabled(enabled)
    return {"kill_switch": orchestrator.kill_switch_service.is_enabled()}
