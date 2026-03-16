"""OpenClaw 工具目录与权限控制。"""

from __future__ import annotations

from apps.agent_orchestrator.tools.schemas import ToolCatalogItem
from apps.agent_orchestrator.tools.tool_registry import ToolRegistry, build_tool_registry


class ToolACL:
    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self.registry = registry or build_tool_registry()

    def is_allowed(self, role: str, tool_name: str) -> bool:
        tool = self.registry.get(tool_name)
        return tool is not None and role in tool.roles

    def list_allowed_tools(self, role: str) -> list[ToolCatalogItem]:
        return [tool.to_catalog_item() for tool in self.registry.list_allowed(role)]

    def catalog(self) -> list[ToolCatalogItem]:
        return [tool.to_catalog_item() for tool in self.registry.catalog()]
