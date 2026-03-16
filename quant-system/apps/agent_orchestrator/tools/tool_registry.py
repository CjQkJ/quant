"""工具注册表。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.agent_orchestrator.tools.schemas import (
    LatestAnalysisOutput,
    MarketContextOutput,
    MonitorStatusToolOutput,
    PreviewAuditDecisionOutput,
    ReplayScenarioInput,
    ReplayScenarioOutput,
    RunPaperCycleOutput,
    StrategyCandidatesOutput,
    StrategySignalOutput,
    SymbolOnlyInput,
    SymbolTimeframeInput,
    ToolCatalogItem,
)
from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from apps.market_data.services.regime_feature_service import RegimeFeatureService
from apps.risk_engine.schemas.risk import AuditDecisionOutput
from apps.strategy_registry.schemas.strategy import StrategySelectionOutput
from apps.strategy_runtime.schemas.signal import StrategySignal
from shared.models.tables import AnalysisReport, StrategySelection, StrategySignalRecord
from shared.schemas.base import BaseSchema
from shared.utils.demo_data import seed_market_data
from shared.utils.state_store import InMemoryStateStore


ToolHandler = Callable[[Session, BaseSchema], BaseSchema]


@dataclass(frozen=True)
class RegisteredTool:
    name: str
    description: str
    risk_level: str
    roles: list[str]
    input_model: type[BaseSchema]
    output_model: type[BaseSchema]
    handler: ToolHandler

    def to_catalog_item(self) -> ToolCatalogItem:
        return ToolCatalogItem(
            name=self.name,
            description=self.description,
            risk_level=self.risk_level,
            roles=self.roles,
            input_schema=self.input_model.__name__,
            output_schema=self.output_model.__name__,
        )


class ToolRegistry:
    def __init__(self, tools: list[RegisteredTool]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    def get(self, name: str) -> RegisteredTool | None:
        return self._tools.get(name)

    def catalog(self) -> list[RegisteredTool]:
        return list(self._tools.values())

    def list_allowed(self, role: str) -> list[RegisteredTool]:
        return [tool for tool in self._tools.values() if role in tool.roles]


def _load_latest_analysis(session: Session, symbol: str) -> AnalysisAgentOutput | None:
    row = session.scalar(select(AnalysisReport).where(AnalysisReport.symbol == symbol).order_by(AnalysisReport.created_at.desc()).limit(1))
    return None if row is None else AnalysisAgentOutput.model_validate(row.raw_payload)


def _load_latest_selection(session: Session, symbol: str) -> StrategySelectionOutput | None:
    row = session.scalar(
        select(StrategySelection)
        .join(AnalysisReport, StrategySelection.analysis_id == AnalysisReport.analysis_id)
        .where(AnalysisReport.symbol == symbol)
        .order_by(StrategySelection.created_at.desc())
        .limit(1)
    )
    return None if row is None else StrategySelectionOutput.model_validate(row.raw_payload)


def _load_latest_strategy_signal(session: Session, symbol: str) -> StrategySignal | None:
    row = session.scalar(
        select(StrategySignalRecord).where(StrategySignalRecord.symbol == symbol).order_by(StrategySignalRecord.created_at.desc()).limit(1)
    )
    return None if row is None else StrategySignal.model_validate(row.raw_payload)


def _handle_market_context(session: Session, request: BaseSchema) -> BaseSchema:
    request = SymbolTimeframeInput.model_validate(request)
    snapshot = RegimeFeatureService().build_snapshot(session, symbol=request.symbol, timeframe=request.timeframe)
    return MarketContextOutput(market_context=snapshot)


def _handle_latest_analysis(session: Session, request: BaseSchema) -> BaseSchema:
    request = SymbolOnlyInput.model_validate(request)
    return LatestAnalysisOutput(analysis=_load_latest_analysis(session, request.symbol))


def _handle_strategy_candidates(session: Session, request: BaseSchema) -> BaseSchema:
    request = SymbolOnlyInput.model_validate(request)
    return StrategyCandidatesOutput(selection=_load_latest_selection(session, request.symbol))


def _handle_strategy_signal(session: Session, request: BaseSchema) -> BaseSchema:
    request = SymbolOnlyInput.model_validate(request)
    return StrategySignalOutput(strategy_signal=_load_latest_strategy_signal(session, request.symbol))


def _handle_preview_audit(session: Session, request: BaseSchema) -> BaseSchema:
    request = SymbolOnlyInput.model_validate(request)
    analysis = _load_latest_analysis(session, request.symbol)
    selection = _load_latest_selection(session, request.symbol)
    strategy_signal = _load_latest_strategy_signal(session, request.symbol)
    if analysis is None or selection is None or strategy_signal is None:
        raise ValueError("缺少最新分析、选策略或策略信号，无法预览审核结果")

    from apps.agent_orchestrator.main import orchestrator

    audit = orchestrator.audit_service.audit(
        session,
        analysis=analysis,
        selection=selection,
        strategy_signal=strategy_signal,
        persist=False,
    )
    return PreviewAuditDecisionOutput(audit=AuditDecisionOutput.model_validate(audit))


def _handle_run_paper_cycle(session: Session, request: BaseSchema) -> BaseSchema:
    request = SymbolTimeframeInput.model_validate(request)
    from apps.agent_orchestrator.main import orchestrator

    result = orchestrator.run_cycle(session, symbol=request.symbol, timeframe=request.timeframe)
    return RunPaperCycleOutput(cycle_result=result)


def _handle_monitor_status(session: Session, request: BaseSchema) -> BaseSchema:
    request = SymbolOnlyInput.model_validate(request)
    from apps.agent_orchestrator.main import orchestrator

    return MonitorStatusToolOutput(monitor_status=orchestrator.monitor_agent.run(session, symbol=request.symbol))


def _handle_run_replay(session: Session, request: BaseSchema) -> BaseSchema:
    request = ReplayScenarioInput.model_validate(request)
    from apps.agent_orchestrator.main import OrchestratorService
    from apps.agent_orchestrator.replay.replay_runner import ReplayRunner
    from apps.strategy_registry.services.registry_service import RegistryService

    fixture_path = Path("tests/fixtures") / request.fixture_name
    if not fixture_path.exists():
        raise ValueError(f"未找到 replay fixture: {request.fixture_name}")

    bars = json.loads(fixture_path.read_text(encoding="utf-8"))
    RegistryService().seed_default_strategies(session)
    seed_market_data(session, mode="trend")
    session.flush()
    summary = ReplayRunner(OrchestratorService(state_store=InMemoryStateStore())).run(
        session,
        bars=bars,
        symbol=request.symbol,
        timeframe=request.timeframe,
        fixture_name=request.fixture_name,
    )
    return ReplayScenarioOutput(replay_summary=summary)


def build_tool_registry() -> ToolRegistry:
    tools = [
        RegisteredTool(
            name="get_market_context",
            description="读取最新市场快照和特征上下文",
            risk_level="low",
            roles=["analyst_agent", "selector_agent", "auditor_agent", "replay_planner_agent", "anomaly_reviewer_agent"],
            input_model=SymbolTimeframeInput,
            output_model=MarketContextOutput,
            handler=_handle_market_context,
        ),
        RegisteredTool(
            name="get_latest_analysis",
            description="读取最新分析结果",
            risk_level="low",
            roles=["analyst_agent", "selector_agent", "auditor_agent", "monitor_agent", "replay_planner_agent", "anomaly_reviewer_agent"],
            input_model=SymbolOnlyInput,
            output_model=LatestAnalysisOutput,
            handler=_handle_latest_analysis,
        ),
        RegisteredTool(
            name="get_strategy_candidates",
            description="读取候选策略与排序结果",
            risk_level="low",
            roles=["selector_agent", "auditor_agent", "anomaly_reviewer_agent"],
            input_model=SymbolOnlyInput,
            output_model=StrategyCandidatesOutput,
            handler=_handle_strategy_candidates,
        ),
        RegisteredTool(
            name="get_strategy_signal",
            description="读取已选策略的运行时信号",
            risk_level="medium",
            roles=["auditor_agent", "executor_agent", "monitor_agent", "anomaly_reviewer_agent"],
            input_model=SymbolOnlyInput,
            output_model=StrategySignalOutput,
            handler=_handle_strategy_signal,
        ),
        RegisteredTool(
            name="preview_audit_decision",
            description="预览审核结果，不直接触发执行",
            risk_level="medium",
            roles=["auditor_agent", "monitor_agent", "anomaly_reviewer_agent"],
            input_model=SymbolOnlyInput,
            output_model=PreviewAuditDecisionOutput,
            handler=_handle_preview_audit,
        ),
        RegisteredTool(
            name="run_paper_cycle",
            description="执行一次受控的 paper trading 周期",
            risk_level="high",
            roles=["executor_agent"],
            input_model=SymbolTimeframeInput,
            output_model=RunPaperCycleOutput,
            handler=_handle_run_paper_cycle,
        ),
        RegisteredTool(
            name="run_paper_execution",
            description="兼容旧名称的 paper trading 执行入口",
            risk_level="high",
            roles=["executor_agent"],
            input_model=SymbolTimeframeInput,
            output_model=RunPaperCycleOutput,
            handler=_handle_run_paper_cycle,
        ),
        RegisteredTool(
            name="get_monitor_status",
            description="读取系统监控状态和风险快照",
            risk_level="medium",
            roles=["monitor_agent", "auditor_agent", "anomaly_reviewer_agent"],
            input_model=SymbolOnlyInput,
            output_model=MonitorStatusToolOutput,
            handler=_handle_monitor_status,
        ),
        RegisteredTool(
            name="run_replay_scenario",
            description="执行历史回放场景",
            risk_level="medium",
            roles=["monitor_agent", "analyst_agent", "replay_planner_agent"],
            input_model=ReplayScenarioInput,
            output_model=ReplayScenarioOutput,
            handler=_handle_run_replay,
        ),
    ]
    return ToolRegistry(tools)
