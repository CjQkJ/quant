"""分析结果汇总。"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput, KeyFactor
from apps.analysis_engine.services.directional_bias_service import DirectionalBiasService
from apps.analysis_engine.services.market_regime_service import MarketRegimeService
from apps.market_data.services.regime_feature_service import RegimeFeatureService
from shared.models.tables import AnalysisReport
from shared.utils.ids import new_analysis_id
from shared.utils.time import utc_now


class SignalSummaryService:
    def __init__(self) -> None:
        self.feature_service = RegimeFeatureService()
        self.regime_service = MarketRegimeService()
        self.bias_service = DirectionalBiasService()

    def analyze(self, session: Session, task_id: str, symbol: str, timeframe: str = "5m") -> AnalysisAgentOutput:
        snapshot = self.feature_service.build_snapshot(session, symbol=symbol, timeframe=timeframe)
        regime = self.regime_service.classify(snapshot)
        bias = self.bias_service.classify(snapshot)

        volatility_level = "high" if snapshot.realized_volatility >= 0.015 else "medium" if snapshot.realized_volatility >= 0.007 else "low"
        liquidity_level = "high" if snapshot.liquidity_score >= 0.7 and snapshot.spread_bps <= 6 else "medium" if snapshot.liquidity_score >= 0.4 else "low"
        confidence = max(
            0.2,
            min(
                0.95,
                0.55 + abs(snapshot.recent_return) * 8 - snapshot.realized_volatility * 2 + snapshot.liquidity_score * 0.15,
            ),
        )

        risk_flags: list[str] = []
        if snapshot.spread_bps > 12:
            risk_flags.append("high_spread")
        if snapshot.source_freshness_seconds > 900:
            risk_flags.append("stale_market_data")
        if snapshot.realized_volatility >= 0.02:
            risk_flags.append("elevated_volatility")
        if snapshot.funding_rate < 0:
            risk_flags.append("negative_funding")

        preferred = {
            "trend": ["trend_following", "breakout_filter"],
            "range": ["mean_reversion", "defensive"],
            "event": ["breakout_filter", "defensive"],
            "high_vol": ["breakout_filter", "defensive"],
        }[regime]
        rejected = ["aggressive_trend_following"] if regime in {"range", "event"} else ["mean_reversion"]

        output = AnalysisAgentOutput(
            task_id=task_id,
            analysis_id=new_analysis_id(),
            exchange=snapshot.exchange,
            symbol=snapshot.symbol,
            timeframe=snapshot.timeframe,
            analysis_time=utc_now(),
            market_regime=regime,
            directional_bias=bias,
            confidence=round(confidence, 4),
            volatility_level=volatility_level,
            liquidity_level=liquidity_level,
            key_factors=[
                KeyFactor(name="recent_return", value=f"{snapshot.recent_return:.4%}", weight=0.35),
                KeyFactor(name="realized_volatility", value=f"{snapshot.realized_volatility:.4%}", weight=0.30),
                KeyFactor(name="funding_rate", value=f"{snapshot.funding_rate:.6f}", weight=0.20),
                KeyFactor(name="spread_bps", value=f"{snapshot.spread_bps:.2f}", weight=0.15),
            ],
            risk_flags=risk_flags,
            preferred_strategy_types=preferred,
            rejected_strategy_types=rejected,
            summary=f"market_regime={regime}, directional_bias={bias}, liquidity={liquidity_level}, confidence={confidence:.2f}",
        )

        row = AnalysisReport(
            analysis_id=output.analysis_id,
            task_id=output.task_id,
            exchange=output.exchange,
            symbol=output.symbol,
            timeframe=output.timeframe,
            regime=output.market_regime,
            bias=output.directional_bias,
            confidence=Decimal(str(output.confidence)),
            volatility_level=output.volatility_level,
            liquidity_level=output.liquidity_level,
            key_factors=[factor.model_dump() for factor in output.key_factors],
            risk_flags=output.risk_flags,
            suggested_strategy_types=output.preferred_strategy_types,
            raw_payload=output.model_dump(mode="json"),
            created_by_agent="analyst_agent",
        )
        session.add(row)
        session.flush()
        return output

