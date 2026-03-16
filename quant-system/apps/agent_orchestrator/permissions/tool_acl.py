"""OpenClaw 工具注册与权限控制。"""

from __future__ import annotations

from shared.schemas.base import BaseSchema


class RegisteredTool(BaseSchema):
    name: str
    description: str
    risk_level: str
    roles: list[str]


TOOL_REGISTRY: dict[str, RegisteredTool] = {
    "get_market_context": RegisteredTool(
        name="get_market_context",
        description="读取最新市场快照和特征上下文",
        risk_level="low",
        roles=["analyst_agent", "selector_agent", "auditor_agent"],
    ),
    "get_latest_analysis": RegisteredTool(
        name="get_latest_analysis",
        description="读取最新分析结果",
        risk_level="low",
        roles=["analyst_agent", "selector_agent", "auditor_agent", "monitor_agent"],
    ),
    "get_strategy_candidates": RegisteredTool(
        name="get_strategy_candidates",
        description="读取候选策略与排序结果",
        risk_level="low",
        roles=["selector_agent", "auditor_agent"],
    ),
    "get_strategy_signal": RegisteredTool(
        name="get_strategy_signal",
        description="读取已选策略的运行时信号",
        risk_level="medium",
        roles=["auditor_agent", "executor_agent", "monitor_agent"],
    ),
    "preview_audit_decision": RegisteredTool(
        name="preview_audit_decision",
        description="预览审核结果，不直接触发执行",
        risk_level="medium",
        roles=["auditor_agent", "monitor_agent"],
    ),
    "run_paper_cycle": RegisteredTool(
        name="run_paper_cycle",
        description="执行一次受控的 paper trading 周期",
        risk_level="high",
        roles=["executor_agent"],
    ),
    "run_paper_execution": RegisteredTool(
        name="run_paper_execution",
        description="兼容旧名称的 paper trading 执行入口",
        risk_level="high",
        roles=["executor_agent"],
    ),
    "get_monitor_status": RegisteredTool(
        name="get_monitor_status",
        description="读取系统监控状态和风险快照",
        risk_level="medium",
        roles=["monitor_agent", "auditor_agent"],
    ),
    "run_replay_scenario": RegisteredTool(
        name="run_replay_scenario",
        description="执行历史回放场景",
        risk_level="medium",
        roles=["monitor_agent", "analyst_agent"],
    ),
}


class ToolACL:
    def is_allowed(self, role: str, tool_name: str) -> bool:
        tool = TOOL_REGISTRY.get(tool_name)
        return tool is not None and role in tool.roles

    def list_allowed_tools(self, role: str) -> list[RegisteredTool]:
        return [tool for tool in TOOL_REGISTRY.values() if role in tool.roles]

    def catalog(self) -> list[RegisteredTool]:
        return list(TOOL_REGISTRY.values())
