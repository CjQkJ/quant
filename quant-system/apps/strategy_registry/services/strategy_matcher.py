"""策略匹配服务。"""

from __future__ import annotations

from collections.abc import Iterable

from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from shared.models.tables import StrategyMetadata


def _normalize_bias_tokens(bias: str) -> set[str]:
    tokens = {bias}
    if "_to_" in bias:
        left, right = bias.split("_to_")
        tokens.add(left)
        tokens.add(right)
    return tokens


class StrategyMatcher:
    def match(
        self,
        strategies: Iterable[StrategyMetadata],
        analysis: AnalysisAgentOutput,
    ) -> list[StrategyMetadata]:
        bias_tokens = _normalize_bias_tokens(analysis.directional_bias)
        matched: list[StrategyMetadata] = []
        for strategy in strategies:
            if analysis.market_regime not in strategy.market_regime_fit:
                continue
            if not bias_tokens.intersection(set(strategy.directional_fit)):
                continue
            matched.append(strategy)
        return matched

