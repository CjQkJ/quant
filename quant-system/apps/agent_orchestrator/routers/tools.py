"""工具目录内部路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from apps.agent_orchestrator.api.dependencies import require_internal_access
from apps.agent_orchestrator.permissions.tool_acl import ToolACL

router = APIRouter(prefix="/tools", tags=["tools"], dependencies=[Depends(require_internal_access)])


@router.get("/catalog")
def get_tool_catalog() -> list[dict]:
    return [tool.model_dump(mode="json") for tool in ToolACL().catalog()]


@router.get("/catalog/{role}")
def get_role_tool_catalog(role: str) -> list[dict]:
    return [tool.model_dump(mode="json") for tool in ToolACL().list_allowed_tools(role)]
