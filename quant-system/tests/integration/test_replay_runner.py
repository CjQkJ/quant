from __future__ import annotations

import json
from pathlib import Path

from apps.agent_orchestrator.main import OrchestratorService
from apps.agent_orchestrator.replay.replay_runner import ReplayRunner
from apps.strategy_registry.services.registry_service import RegistryService
from shared.utils.state_store import InMemoryStateStore
from tests.helpers import seed_market_data


def test_replay_runner(session):
    RegistryService().seed_default_strategies(session)
    seed_market_data(session, mode="trend")
    bars = json.loads(Path("tests/fixtures/replay_bars.json").read_text(encoding="utf-8"))
    runner = ReplayRunner(OrchestratorService(state_store=InMemoryStateStore()))
    summary = runner.run(session, bars=bars, symbol="BTCUSDT", timeframe="5m")
    assert summary.cycle_count == len(bars)
    assert len(summary.cycle_results) == len(bars)
    assert summary.analysis_version
    assert summary.risk_policy_version
