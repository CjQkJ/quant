from __future__ import annotations

from apps.risk_engine.services.exposure_service import ExposureService
from apps.risk_engine.services.global_risk_service import GlobalRiskService
from apps.risk_engine.services.kill_switch_service import KillSwitchService
from apps.risk_engine.services.monitor_service import MonitorService
from tests.helpers import seed_market_data


def test_monitor_reports_signal_and_analysis_freshness(session, state_store):
    seed_market_data(session, mode="trend")
    monitor = MonitorService(
        kill_switch_service=KillSwitchService(state_store),
        global_risk_service=GlobalRiskService(state_store),
        exposure_service=ExposureService(GlobalRiskService(state_store)),
    )
    output = monitor.run_cycle(session, symbol="BTCUSDT")
    freshness = {item.source: item for item in output.source_freshness}
    assert freshness["analysis_output"].missing is True
    assert freshness["strategy_signal"].missing is True
    suggestion_actions = {item.action for item in output.suggestions}
    assert "suggest_replay" in suggestion_actions
