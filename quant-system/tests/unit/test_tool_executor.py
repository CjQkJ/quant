from __future__ import annotations

import pytest
from sqlalchemy import select

from apps.agent_orchestrator.agents.output_guard import AgentOutputGuard
from apps.agent_orchestrator.tools.schema_guard import SchemaGuardError
from apps.agent_orchestrator.tools.tool_executor import ToolExecutor
from apps.agent_orchestrator.tools.tool_registry import RegisteredTool, ToolRegistry
from apps.agent_orchestrator.tools.schemas import MarketContextOutput, SymbolOnlyInput, SymbolTimeframeInput
from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from shared.models.tables import TaskEventLog
from tests.helpers import seed_market_data


def test_tool_executor_denied_logs_event(session):
    executor = ToolExecutor()

    with pytest.raises(PermissionError):
        executor.execute(session, role="executor_agent", tool_name="get_latest_analysis", payload={"symbol": "BTCUSDT"}, task_id="task_acl")

    event = session.scalar(select(TaskEventLog).where(TaskEventLog.task_id == "task_acl"))
    assert event is not None
    assert event.event_type == "tool_acl_denied"


def test_tool_executor_output_invalid_logs_event(session):
    def invalid_handler(session, request):
        return {}

    registry = ToolRegistry(
        [
            RegisteredTool(
                name="invalid_tool",
                description="测试无效输出",
                risk_level="low",
                roles=["analyst_agent"],
                input_model=SymbolOnlyInput,
                output_model=MarketContextOutput,
                handler=invalid_handler,
            )
        ]
    )
    executor = ToolExecutor(registry=registry)

    with pytest.raises(SchemaGuardError):
        executor.execute(session, role="analyst_agent", tool_name="invalid_tool", payload={"symbol": "BTCUSDT"}, task_id="task_invalid")

    event = session.scalar(select(TaskEventLog).where(TaskEventLog.task_id == "task_invalid"))
    assert event is not None
    assert event.event_type == "tool_output_invalid"


def test_openclaw_agent_invalid_output_logs_event(session):
    with pytest.raises(ValueError):
        AgentOutputGuard().validate(
            session,
            task_id="task_openclaw",
            agent_name="analyst_agent",
            expected_schema=AnalysisAgentOutput,
            output={"task_id": "task_openclaw"},
            source_kind="openclaw",
        )

    event = session.scalar(select(TaskEventLog).where(TaskEventLog.task_id == "task_openclaw"))
    assert event is not None
    assert event.event_type == "openclaw_agent_output_invalid"


def test_tool_executor_success(session):
    seed_market_data(session, mode="trend")
    executor = ToolExecutor()

    task_id, output = executor.execute(
        session,
        role="analyst_agent",
        tool_name="get_market_context",
        payload=SymbolTimeframeInput(symbol="BTCUSDT", timeframe="5m"),
        task_id="task_success",
    )

    assert task_id == "task_success"
    assert output.market_context.symbol == "BTCUSDT"
