from __future__ import annotations

from apps.agent_orchestrator.agents.selector_agent import SelectorAgent
from apps.analysis_engine.services.signal_summary_service import SignalSummaryService
from apps.risk_engine.services.audit_service import AuditService
from apps.risk_engine.services.exposure_service import ExposureService
from apps.risk_engine.services.global_risk_service import GlobalRiskService
from apps.risk_engine.services.kill_switch_service import KillSwitchService
from apps.risk_engine.services.strategy_applicability_service import StrategyApplicabilityService
from apps.strategy_runtime.services.runtime_service import StrategyRuntimeService
from apps.execution_engine.services.account_state_service import AccountStateService
from tests.helpers import seed_market_data


def test_kill_switch_forces_reject(session, state_store):
    from apps.strategy_registry.services.registry_service import RegistryService

    RegistryService().seed_default_strategies(session)
    seed_market_data(session, mode="trend")
    analysis = SignalSummaryService().analyze(session, task_id="task_x", symbol="BTCUSDT")
    selection = SelectorAgent().run(session, analysis)
    strategy_signal = StrategyRuntimeService(AccountStateService(state_store)).get_strategy_signal(session, analysis, selection)
    kill_switch = KillSwitchService(state_store)
    kill_switch.set_enabled(True)
    audit = AuditService(
        kill_switch_service=kill_switch,
        global_risk_service=GlobalRiskService(state_store),
        exposure_service=ExposureService(GlobalRiskService(state_store)),
        applicability_service=StrategyApplicabilityService(),
    ).audit(session, analysis, selection, strategy_signal)
    assert audit.decision == "reject"


def test_low_confidence_requests_more_context(session, state_store):
    from apps.strategy_registry.services.registry_service import RegistryService

    RegistryService().seed_default_strategies(session)
    seed_market_data(session, mode="low_confidence")
    analysis = SignalSummaryService().analyze(session, task_id="task_low", symbol="BTCUSDT")
    analysis = analysis.model_copy(update={"confidence": 0.35, "liquidity_level": "medium", "risk_flags": []})
    selection = SelectorAgent().run(session, analysis)
    strategy_signal = StrategyRuntimeService(AccountStateService(state_store)).get_strategy_signal(session, analysis, selection)
    audit = AuditService(
        kill_switch_service=KillSwitchService(state_store),
        global_risk_service=GlobalRiskService(state_store),
        exposure_service=ExposureService(GlobalRiskService(state_store)),
        applicability_service=StrategyApplicabilityService(),
    ).audit(session, analysis, selection, strategy_signal)
    assert audit.decision == "observe_only"
    assert audit.next_action == "request_more_context"
    assert "refresh_strategy_signal" in audit.context_requirements
