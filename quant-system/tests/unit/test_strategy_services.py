from __future__ import annotations

from datetime import datetime, timezone

from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput, KeyFactor
from apps.strategy_registry.services.ranking_service import RankingService
from apps.strategy_registry.services.registry_service import RegistryService
from apps.strategy_registry.services.strategy_matcher import StrategyMatcher


def build_analysis(regime: str = "range", bias: str = "neutral_to_short", confidence: float = 0.72) -> AnalysisAgentOutput:
    return AnalysisAgentOutput(
        task_id="task_x",
        analysis_id="analysis_x",
        exchange="binance",
        symbol="BTCUSDT",
        timeframe="5m",
        analysis_time=datetime.now(timezone.utc),
        market_regime=regime,
        directional_bias=bias,
        confidence=confidence,
        volatility_level="medium",
        liquidity_level="high",
        key_factors=[KeyFactor(name="x", value="y", weight=1.0)],
        risk_flags=[],
        preferred_strategy_types=["mean_reversion"],
        rejected_strategy_types=[],
        summary="ok",
    )


def test_matcher_and_ranking(session):
    RegistryService().seed_default_strategies(session)
    strategies = RegistryService().list_enabled(session, "BTCUSDT", "5m")
    matched = StrategyMatcher().match(strategies, build_analysis())
    ranked = RankingService().rank(matched, build_analysis())
    assert matched
    assert ranked[0].strategy_id == "mr_btc_5m_v1"
