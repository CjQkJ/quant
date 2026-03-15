"""方向偏向判断。"""

from __future__ import annotations

from apps.market_data.schemas.feature import MarketFeatureSnapshot
from shared.models.enums import DirectionalBias


class DirectionalBiasService:
    def classify(self, snapshot: MarketFeatureSnapshot) -> str:
        ret = snapshot.recent_return
        funding = snapshot.funding_rate
        if ret >= 0.006 and funding >= 0:
            return DirectionalBias.LONG
        if ret <= -0.006 and funding <= 0:
            return DirectionalBias.SHORT
        if ret < 0 and funding <= 0:
            return DirectionalBias.NEUTRAL_TO_SHORT
        if ret > 0 and funding >= 0:
            return DirectionalBias.NEUTRAL_TO_LONG
        return DirectionalBias.NEUTRAL

