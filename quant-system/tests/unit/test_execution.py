from __future__ import annotations

from apps.agent_orchestrator.agents.selector_agent import SelectorAgent
from apps.analysis_engine.services.signal_summary_service import SignalSummaryService
from apps.execution_engine.services.account_state_service import AccountStateService
from apps.execution_engine.services.order_executor import OrderExecutor
from apps.execution_engine.services.order_planner import OrderPlanner
from apps.market_data.services.orderbook_service import OrderBookService
from apps.risk_engine.services.audit_service import AuditService
from apps.risk_engine.services.exposure_service import ExposureService
from apps.risk_engine.services.global_risk_service import GlobalRiskService
from apps.risk_engine.services.kill_switch_service import KillSwitchService
from apps.risk_engine.services.strategy_applicability_service import StrategyApplicabilityService
from apps.strategy_registry.services.registry_service import RegistryService
from apps.strategy_runtime.services.runtime_service import StrategyRuntimeService
from tests.helpers import seed_market_data


def test_paper_execution_updates_account(session, state_store):
    RegistryService().seed_default_strategies(session)
    seed_market_data(session, mode="trend")
    analysis = SignalSummaryService().analyze(session, task_id="task_x", symbol="BTCUSDT")
    selection = SelectorAgent().run(session, analysis)
    global_risk = GlobalRiskService(state_store)
    kill_switch = KillSwitchService(state_store)
    strategy_signal = StrategyRuntimeService(AccountStateService(state_store)).get_strategy_signal(session, analysis, selection)
    audit = AuditService(
        kill_switch_service=kill_switch,
        global_risk_service=global_risk,
        exposure_service=ExposureService(global_risk),
        applicability_service=StrategyApplicabilityService(),
    ).audit(session, analysis, selection, strategy_signal)

    orderbook = OrderBookService().latest(session, "BTCUSDT")
    planner = OrderPlanner(AccountStateService(state_store))
    orders = planner.plan(session, analysis, audit, strategy_signal, orderbook)
    result = OrderExecutor(AccountStateService(state_store), kill_switch).execute(
        session,
        task_id=analysis.task_id,
        audit=audit,
        planned_orders=orders,
        best_bid=float(orderbook.best_bid),
        best_ask=float(orderbook.best_ask),
        strategy_signal_id=strategy_signal.signal_id,
        symbol=analysis.symbol,
        exchange=analysis.exchange,
    )
    assert result.execution_status == "filled"
    account = AccountStateService(state_store).get()
    assert "cash_balance" in account
    assert result.account_snapshot.market_type == "futures"
