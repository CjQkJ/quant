"""回放内部路由。"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from apps.agent_orchestrator.api.dependencies import require_internal_access
from apps.agent_orchestrator.agents.replay_planner_agent import ReplayPlannerAgent
from apps.agent_orchestrator.replay.replay_reporter import ReplayReporter
from apps.agent_orchestrator.replay.replay_runner import ReplayRunner
from apps.agent_orchestrator.schemas.replay_plan import ReplayPlannerInput
from apps.strategy_registry.services.registry_service import RegistryService
from shared.db.session import session_scope
from shared.utils.demo_data import seed_market_data

router = APIRouter(prefix="/replay", tags=["replay"], dependencies=[Depends(require_internal_access)])


@router.post("/run-fixture")
def run_replay_fixture(fixture_name: str = "replay_bars.json", symbol: str = "BTCUSDT", timeframe: str = "5m") -> dict:
    from apps.agent_orchestrator.main import OrchestratorService
    from shared.utils.state_store import InMemoryStateStore

    fixture_path = Path("tests/fixtures") / fixture_name
    if not fixture_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"未找到 fixture: {fixture_name}")

    bars = json.loads(fixture_path.read_text(encoding="utf-8"))
    runner = ReplayRunner(OrchestratorService(state_store=InMemoryStateStore()))
    with session_scope() as session:
        RegistryService().seed_default_strategies(session)
        seed_market_data(session, mode="trend")
        session.commit()
        result = runner.run(session, bars=bars, symbol=symbol, timeframe=timeframe, fixture_name=fixture_name)
        session.commit()
        return result.model_dump(mode="json")


@router.get("/plan")
def get_replay_plan(symbol: str = "BTCUSDT", timeframe: str = "5m", fixture_name: str = "replay_bars.json") -> dict:
    plan = ReplayPlannerAgent().run(ReplayPlannerInput(symbol=symbol, timeframe=timeframe, fixture_name=fixture_name))
    return plan.model_dump(mode="json")


@router.get("/report/{run_id}")
def get_replay_report(run_id: str) -> dict:
    from shared.models.tables import ReplayRun
    from apps.agent_orchestrator.schemas.orchestration import ReplayRunSummary

    with session_scope() as session:
        row = session.scalar(select(ReplayRun).where(ReplayRun.run_id == run_id).limit(1))
        if row is None or row.summary_json is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"未找到 replay run: {run_id}")
        summary = ReplayRunSummary.model_validate(row.summary_json)
        return {"run_id": run_id, "markdown": ReplayReporter().to_markdown(summary)}
