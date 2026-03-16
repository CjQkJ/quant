"""市场数据内部路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select

from apps.agent_orchestrator.api.dependencies import require_internal_access
from apps.market_data.services.regime_feature_service import RegimeFeatureService
from shared.db.session import session_scope
from shared.models.tables import AnalysisReport, StrategySelection

router = APIRouter(prefix="/market-data", tags=["market-data"], dependencies=[Depends(require_internal_access)])


@router.get("/context")
def get_market_context(symbol: str = "BTCUSDT", timeframe: str = "5m") -> dict:
    with session_scope() as session:
        snapshot = RegimeFeatureService().build_snapshot(session, symbol=symbol, timeframe=timeframe)
        return snapshot.model_dump(mode="json")


@router.get("/latest-analysis")
def get_latest_analysis(symbol: str = "BTCUSDT") -> dict | None:
    with session_scope() as session:
        row = session.scalar(
            select(AnalysisReport).where(AnalysisReport.symbol == symbol).order_by(AnalysisReport.created_at.desc()).limit(1)
        )
        return None if row is None else row.raw_payload


@router.get("/strategy-candidates")
def get_strategy_candidates(symbol: str = "BTCUSDT") -> dict | None:
    with session_scope() as session:
        row = session.scalar(
            select(StrategySelection).where(StrategySelection.task_id.is_not(None)).order_by(StrategySelection.created_at.desc()).limit(1)
        )
        return None if row is None else row.raw_payload
