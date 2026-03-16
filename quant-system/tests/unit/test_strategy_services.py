from __future__ import annotations

from datetime import datetime, timezone

from apps.agent_orchestrator.agents.selector_agent import SelectorAgent
from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput, KeyFactor
from apps.strategy_registry.services.ranking_service import RankingService
from apps.strategy_registry.services.registry_service import RegistryService
from apps.strategy_registry.services.strategy_matcher import StrategyMatcher
from apps.strategy_runtime.registry import StrategyRuntimeRegistry
from shared.constants.versions import ANALYSIS_VERSION


def build_analysis(regime: str = "range", bias: str = "neutral_to_short", confidence: float = 0.72) -> AnalysisAgentOutput:
    return AnalysisAgentOutput(
        task_id="task_x",
        analysis_id="analysis_x",
        analysis_version=ANALYSIS_VERSION,
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


def test_selector_produces_candidate_hierarchy(session):
    RegistryService().seed_default_strategies(session)
    analysis = build_analysis()
    selection = SelectorAgent().run(session, analysis)
    assert selection.fallback_candidate is not None
    assert selection.challenger_candidate is not None
    assert selection.no_trade_candidate is not None
    assert selection.no_trade_candidate.strategy_type == "defensive"


def test_strategy_runtime_registry_routes_by_strategy(session):
    RegistryService().seed_default_strategies(session)
    trend_strategy = RegistryService().get_by_strategy_id(session, "trend_long_btc_5m_v1")
    defensive_strategy = RegistryService().get_by_strategy_id(session, "defensive_no_trade_btc_5m_v1")
    registry = StrategyRuntimeRegistry()
    assert registry.get_runtime(trend_strategy).__class__.__name__ == "TrendLongRuntime"
    assert registry.get_runtime(defensive_strategy).__class__.__name__ == "DefensiveNoTradeRuntime"
