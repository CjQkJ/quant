"""监控内部路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from apps.agent_orchestrator.api.dependencies import require_internal_access
from apps.agent_orchestrator.agents.anomaly_reviewer_agent import AnomalyReviewerAgent
from apps.agent_orchestrator.schemas.anomaly_review import AnomalyReviewerInput
from shared.db.session import session_scope

router = APIRouter(prefix="/monitor", tags=["monitor"], dependencies=[Depends(require_internal_access)])


@router.get("/status")
def get_monitor_status(symbol: str = "BTCUSDT") -> dict:
    from apps.agent_orchestrator.main import orchestrator

    with session_scope() as session:
        result = orchestrator.monitor_agent.run(session, symbol=symbol)
        session.commit()
        return result.model_dump(mode="json")


@router.get("/anomaly-review/{task_id}")
def get_anomaly_review(task_id: str, symbol: str = "BTCUSDT", lookback_limit: int = 20) -> dict:
    with session_scope() as session:
        result = AnomalyReviewerAgent().run(
            session,
            AnomalyReviewerInput(task_id=task_id, symbol=symbol, lookback_limit=lookback_limit, access_mode="read_only"),
        )
        return result.model_dump(mode="json")
