"""监控内部路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from apps.agent_orchestrator.api.dependencies import require_internal_access
from shared.db.session import session_scope

router = APIRouter(prefix="/monitor", tags=["monitor"], dependencies=[Depends(require_internal_access)])


@router.get("/status")
def get_monitor_status(symbol: str = "BTCUSDT") -> dict:
    from apps.agent_orchestrator.main import orchestrator

    with session_scope() as session:
        result = orchestrator.monitor_agent.run(session, symbol=symbol)
        session.commit()
        return result.model_dump(mode="json")
