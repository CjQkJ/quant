from __future__ import annotations

import json
from pathlib import Path

from apps.agent_orchestrator.main import OrchestratorService
from apps.agent_orchestrator.replay.replay_reporter import ReplayReporter
from apps.agent_orchestrator.replay.replay_runner import ReplayRunner
from apps.strategy_registry.services.registry_service import RegistryService
from shared.utils.state_store import InMemoryStateStore
from tests.helpers import seed_market_data


def test_replay_summary_contains_version_matrix_and_final_metrics(session):
    RegistryService().seed_default_strategies(session)
    seed_market_data(session, mode="trend")
    bars = json.loads(Path("tests/fixtures/replay_bars.json").read_text(encoding="utf-8"))
    summary = ReplayRunner(OrchestratorService(state_store=InMemoryStateStore())).run(
        session,
        bars=bars,
        symbol="BTCUSDT",
        timeframe="5m",
    )
    assert summary.version_matrix.analysis_version == summary.analysis_version
    assert summary.final_equity >= 0
    assert summary.total_fee_paid >= 0
    assert summary.avg_slippage_bps >= 0


def test_replay_reporter_outputs_markdown(session):
    RegistryService().seed_default_strategies(session)
    seed_market_data(session, mode="trend")
    bars = json.loads(Path("tests/fixtures/replay_bars.json").read_text(encoding="utf-8"))
    summary = ReplayRunner(OrchestratorService(state_store=InMemoryStateStore())).run(
        session,
        bars=bars,
        symbol="BTCUSDT",
        timeframe="5m",
    )
    markdown = ReplayReporter().to_markdown(summary)
    assert "# Replay Summary" in markdown
    assert summary.run_id in markdown
