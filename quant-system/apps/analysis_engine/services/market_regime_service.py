"""市场状态判断。"""

from __future__ import annotations

from apps.market_data.schemas.feature import MarketFeatureSnapshot
from shared.models.enums import MarketRegime


class MarketRegimeService:
    def classify(self, snapshot: MarketFeatureSnapshot) -> str:
        if snapshot.realized_volatility >= 0.02 and abs(snapshot.recent_return) >= 0.015:
            return MarketRegime.EVENT
        if snapshot.realized_volatility >= 0.015:
            return MarketRegime.HIGH_VOL
        if abs(snapshot.recent_return) >= 0.006:
            return MarketRegime.TREND
        return MarketRegime.RANGE

