"""策略排序服务。"""

from __future__ import annotations

from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from apps.strategy_registry.schemas.strategy import RankedCandidate
from shared.models.tables import StrategyMetadata


class RankingService:
    def rank(
        self,
        strategies: list[StrategyMetadata],
        analysis: AnalysisAgentOutput,
    ) -> list[RankedCandidate]:
        candidates: list[RankedCandidate] = []
        for strategy in strategies:
            score = 0.0
            if analysis.market_regime in strategy.market_regime_fit:
                score += 0.35
            if analysis.directional_bias in strategy.directional_fit:
                score += 0.25
            elif any(token in strategy.directional_fit for token in analysis.directional_bias.split("_to_")):
                score += 0.15
            score += min(float(strategy.priority) / 20.0, 0.15)
            score += min(analysis.confidence * 0.15, 0.15)
            if strategy.strategy_type == "defensive" and analysis.confidence < 0.45:
                score += 0.20
            if strategy.strategy_type == "breakout_filter" and analysis.market_regime in {"event", "high_vol"}:
                score += 0.10
            candidates.append(
                RankedCandidate(
                    strategy_id=strategy.strategy_id,
                    strategy_name=strategy.strategy_name,
                    fit_score=round(min(score, 0.99), 4),
                    reason=f"regime={analysis.market_regime}, bias={analysis.directional_bias}, priority={strategy.priority}",
                    strategy_type=strategy.strategy_type,
                )
            )
        return sorted(candidates, key=lambda item: item.fit_score, reverse=True)

