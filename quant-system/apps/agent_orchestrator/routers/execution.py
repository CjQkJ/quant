"""执行内部路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from apps.agent_orchestrator.api.dependencies import require_internal_access
from shared.config.settings import get_settings
from shared.db.session import session_scope
from shared.models.tables import ExecutionOrder

router = APIRouter(prefix="/execution", tags=["execution"], dependencies=[Depends(require_internal_access)])


@router.get("/account")
def get_account_snapshot() -> dict:
    from apps.agent_orchestrator.main import orchestrator

    return orchestrator.account_state_service.build_snapshot().model_dump(mode="json")


@router.get("/orders")
def list_execution_orders(limit: int = 20) -> list[dict]:
    with session_scope() as session:
        rows = session.scalars(select(ExecutionOrder).order_by(ExecutionOrder.created_at.desc()).limit(limit)).all()
        return [
            {
                "exec_order_id": row.exec_order_id,
                "symbol": row.symbol,
                "status": row.status,
                "market_type": row.market_type,
                "account_mode": row.account_mode,
                "avg_fill_price": float(row.avg_fill_price or 0),
                "filled_qty": float(row.filled_qty),
            }
            for row in rows
        ]


@router.post("/live/submit")
def submit_live_order() -> dict:
    settings = get_settings()
    if not settings.enable_live_execution:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="live execution 默认关闭")
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="第二阶段尚未开放 live execution")
