"""未平仓量服务。"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from apps.market_data.schemas.market import DerivativesMetricPayload
from shared.models.tables import MarketDerivativesMetric


class OIService:
    metric_type = "open_interest"

    def normalize(self, exchange: str, symbol: str, raw_oi: dict) -> DerivativesMetricPayload:
        ts = raw_oi.get("timestamp") or int(datetime.now(timezone.utc).timestamp() * 1000)
        value = raw_oi.get("openInterestAmount") or raw_oi.get("openInterest") or raw_oi.get("amount") or 0.0
        return DerivativesMetricPayload(
            exchange=exchange,
            symbol=symbol,
            metric_time=datetime.fromtimestamp(ts / 1000, timezone.utc),
            metric_type=self.metric_type,
            metric_value=float(value),
            extra_json=raw_oi,
            source="binance_rest",
        )

    def save(self, session: Session, payload: DerivativesMetricPayload) -> MarketDerivativesMetric:
        row = MarketDerivativesMetric(
            exchange=payload.exchange,
            symbol=payload.symbol,
            metric_time=payload.metric_time,
            metric_type=payload.metric_type,
            metric_value=Decimal(str(payload.metric_value)),
            extra_json=payload.extra_json,
            source=payload.source,
        )
        session.add(row)
        session.flush()
        return row
