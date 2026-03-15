"""OpenClaw 工具权限矩阵。"""

from __future__ import annotations


ROLE_TOOL_MATRIX = {
    "analyst_agent": {"read_market_data", "read_orderbook", "read_derivatives_metrics"},
    "selector_agent": {"read_strategy_registry", "read_analysis_report"},
    "auditor_agent": {"read_analysis_report", "read_strategy_selection", "read_risk_state"},
    "executor_agent": {"read_audit_decision", "run_paper_execution"},
    "monitor_agent": {"read_system_state", "read_execution_orders", "raise_alert"},
}


class ToolACL:
    def is_allowed(self, role: str, tool_name: str) -> bool:
        return tool_name in ROLE_TOOL_MATRIX.get(role, set())

