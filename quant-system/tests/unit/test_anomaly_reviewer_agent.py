from __future__ import annotations

from sqlalchemy import select

from apps.agent_orchestrator.agents.anomaly_reviewer_agent import AnomalyReviewerAgent
from apps.agent_orchestrator.main import OrchestratorService
from apps.agent_orchestrator.schemas.anomaly_review import AnomalyReviewerInput
from apps.strategy_registry.services.registry_service import RegistryService
from shared.models.tables import TaskEventLog
from shared.utils.state_store import InMemoryStateStore
from tests.helpers import seed_market_data


def test_anomaly_reviewer_agent_is_read_only(session):
    RegistryService().seed_default_strategies(session)
    seed_market_data(session, mode="trend")
    orchestrator = OrchestratorService(state_store=InMemoryStateStore())
    result = orchestrator.run_cycle(session, symbol="BTCUSDT", timeframe="5m")
    events_before = session.scalars(select(TaskEventLog)).all()

    review = AnomalyReviewerAgent().run(
        session,
        AnomalyReviewerInput(task_id=result.task_id, symbol="BTCUSDT", lookback_limit=10, access_mode="read_only"),
    )

    events_after = session.scalars(select(TaskEventLog)).all()
    assert review.access_mode == "read_only"
    assert review.event_count == len(review.reviewed_events)
    assert len(events_before) == len(events_after)
