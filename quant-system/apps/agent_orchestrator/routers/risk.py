"""风控内部路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from apps.agent_orchestrator.api.dependencies import require_internal_access
from shared.config.risk_policy import get_risk_policy

router = APIRouter(prefix="/risk", tags=["risk"], dependencies=[Depends(require_internal_access)])


@router.get("/policy")
def get_risk_policy_config() -> dict:
    return get_risk_policy().model_dump(mode="json")
