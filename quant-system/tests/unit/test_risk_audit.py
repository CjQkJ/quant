from __future__ import annotations

from apps.agent_orchestrator.agents.selector_agent import SelectorAgent
from apps.analysis_engine.services.signal_summary_service import SignalSummaryService
from apps.risk_engine.services.audit_service import AuditService
from apps.risk_engine.services.exposure_service import ExposureService
from apps.risk_engine.services.global_risk_service import GlobalRiskService
from apps.risk_engine.services.kill_switch_service import KillSwitchService
from apps.risk_engine.services.strategy_applicability_service import StrategyApplicabilityService
from tests.helpers import seed_market_data


def test_kill_switch_forces_reject(session, state_store):
    from apps.strategy_registry.services.registry_service import RegistryService

    RegistryService().seed_default_strategies(session)
    seed_market_data(session, mode="trend")
    analysis = SignalSummaryService().analyze(session, task_id="task_x", symbol="BTCUSDT")
    selection = SelectorAgent().run(session, analysis)
    kill_switch = KillSwitchService(state_store)
    kill_switch.set_enabled(True)
    audit = AuditService(
        kill_switch_service=kill_switch,
        global_risk_service=GlobalRiskService(state_store),
        exposure_service=ExposureService(GlobalRiskService(state_store)),
        applicability_service=StrategyApplicabilityService(),
    ).audit(session, analysis, selection)
    assert audit.decision == "reject"
