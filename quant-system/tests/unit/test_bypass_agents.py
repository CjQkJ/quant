from __future__ import annotations

from apps.agent_orchestrator.agents.replay_planner_agent import ReplayPlannerAgent
from apps.agent_orchestrator.agents.tool_gap_agent import ToolGapAgent
from apps.agent_orchestrator.schemas.replay_plan import ReplayPlannerInput
from apps.agent_orchestrator.schemas.tool_gap import ToolGapInput
from shared.models.tables import TaskEventLog


def test_replay_planner_returns_baseline_versions():
    output = ReplayPlannerAgent().run(ReplayPlannerInput())
    assert output.baseline.analysis_version
    assert output.comparison_targets


def test_tool_gap_agent_only_reports(session):
    session.add(
        TaskEventLog(
            task_id="task_gap",
            event_type="tool_output_invalid",
            event_source="get_market_context",
            event_payload={"detail": "invalid"},
            message="测试事件",
            level="error",
        )
    )
    session.flush()
    output = ToolGapAgent().run(session, ToolGapInput(lookback_limit=10))
    assert output.gap_items
    assert all(item.recommendation for item in output.gap_items)
