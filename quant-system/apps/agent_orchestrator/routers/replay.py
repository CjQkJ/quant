"""回放内部路由。"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from apps.agent_orchestrator.api.dependencies import require_internal_access
from apps.agent_orchestrator.replay.replay_runner import ReplayRunner
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
