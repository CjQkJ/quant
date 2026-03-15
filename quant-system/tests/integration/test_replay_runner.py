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
    results = runner.run(session, bars=bars, symbol="BTCUSDT", timeframe="5m")
    assert len(results) == len(bars)
    assert all("analysis" in item for item in results)
