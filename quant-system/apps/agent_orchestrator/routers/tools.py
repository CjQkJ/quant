"""工具目录内部路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from apps.agent_orchestrator.agents.tool_gap_agent import ToolGapAgent
from apps.agent_orchestrator.api.dependencies import require_internal_access
from apps.agent_orchestrator.permissions.tool_acl import ToolACL
from apps.agent_orchestrator.schemas.tool_gap import ToolGapInput
from apps.agent_orchestrator.tools.schemas import ToolExecutionEnvelope
from apps.agent_orchestrator.tools.tool_executor import ToolExecutor
from shared.db.session import session_scope

router = APIRouter(prefix="/tools", tags=["tools"], dependencies=[Depends(require_internal_access)])


@router.get("/catalog")
def get_tool_catalog() -> list[dict]:
    return [tool.model_dump(mode="json") for tool in ToolACL().catalog()]


@router.get("/catalog/{role}")
def get_role_tool_catalog(role: str) -> list[dict]:
    return [tool.model_dump(mode="json") for tool in ToolACL().list_allowed_tools(role)]


@router.post("/execute/{role}/{tool_name}")
def execute_tool(role: str, tool_name: str, request: ToolExecutionEnvelope) -> dict:
    with session_scope() as session:
        task_id, result = ToolExecutor().execute(
            session,
            role=role,
            tool_name=tool_name,
            payload=request.payload,
            task_id=request.task_id,
        )
        session.commit()
        return {"task_id": task_id, "tool_name": tool_name, "result": result.model_dump(mode="json")}


@router.get("/gap-report")
def get_tool_gap_report(lookback_limit: int = 100) -> dict:
    with session_scope() as session:
        result = ToolGapAgent().run(session, ToolGapInput(lookback_limit=lookback_limit))
        return result.model_dump(mode="json")
