from __future__ import annotations

from sqlalchemy import select

from apps.agent_orchestrator.main import OrchestratorService
from apps.strategy_registry.services.registry_service import RegistryService
from shared.models.tables import TaskEventLog
from shared.utils.state_store import InMemoryStateStore
from tests.helpers import seed_market_data


def test_orchestrator_approve_flow(session):
    RegistryService().seed_default_strategies(session)
    seed_market_data(session, mode="trend")
    orchestrator = OrchestratorService(state_store=InMemoryStateStore())
    result = orchestrator.run_cycle(session, symbol="BTCUSDT", timeframe="5m")
    assert result.audit.decision in {"approve", "downgrade"}
    assert result.execution.execution_status in {"filled", "skipped"}
    events = session.scalars(select(TaskEventLog)).all()
    assert len(events) >= 5


def test_orchestrator_reject_flow(session):
    RegistryService().seed_default_strategies(session)
    seed_market_data(session, mode="trend")
    state_store = InMemoryStateStore()
    state_store.set_bool("runtime:kill_switch", True)
    orchestrator = OrchestratorService(state_store=state_store)
    result = orchestrator.run_cycle(session, symbol="BTCUSDT", timeframe="5m")
    assert result.audit.decision == "reject"
    assert result.execution.execution_status == "skipped"


def test_orchestrator_observe_only_flow(session):
    RegistryService().seed_default_strategies(session)
    seed_market_data(session, mode="low_confidence")
    orchestrator = OrchestratorService(state_store=InMemoryStateStore())
    result = orchestrator.run_cycle(session, symbol="BTCUSDT", timeframe="5m")
    assert result.audit.decision in {"observe_only", "downgrade", "reject"}
