"""演示和测试共用的基线数据填充。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from apps.market_data.schemas.market import DerivativesMetricPayload, OHLCVPayload, OrderBookSnapshotPayload, OrderLevel
from apps.market_data.services.funding_service import FundingService
from apps.market_data.services.ohlcv_service import OHLCVService
from apps.market_data.services.oi_service import OIService
from apps.market_data.services.orderbook_service import OrderBookService


def seed_market_data(session: Session, mode: str = "trend") -> None:
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    ohlcv_service = OHLCVService()
    orderbook_service = OrderBookService()
    funding_service = FundingService()
    oi_service = OIService()

    bars: list[OHLCVPayload] = []
    base_price = 71000.0
    for index in range(30):
        open_time = now - timedelta(minutes=(30 - index) * 5)
        close_time = open_time + timedelta(minutes=5)
        if mode == "trend":
            close = base_price + index * 20
        elif mode == "low_confidence":
            close = base_price + (120 if index % 2 == 0 else -120)
        else:
            close = base_price - index * 15
        bars.append(
            OHLCVPayload(
                exchange="binance",
                symbol="BTCUSDT",
                timeframe="5m",
                open_time=open_time,
                close_time=close_time,
                open=close - 10,
                high=close + 15,
                low=close - 15,
                close=close,
                volume=100 + index,
                quote_volume=(100 + index) * close,
                trade_count=1000 + index,
                source="fixture",
            )
        )
    ohlcv_service.save_many(session, bars)

    if mode == "low_confidence":
        best_bid = 70990.0
        best_ask = 71020.0
        bid_depth = [OrderLevel(price=70990.0, qty=1.0)]
        ask_depth = [OrderLevel(price=71020.0, qty=1.2)]
        funding_rate = -0.0002
        open_interest = 1200.0
    else:
        best_bid = 71580.0
        best_ask = 71582.0
        bid_depth = [OrderLevel(price=71580.0, qty=80.0), OrderLevel(price=71579.0, qty=60.0)]
        ask_depth = [OrderLevel(price=71582.0, qty=75.0), OrderLevel(price=71583.0, qty=55.0)]
        funding_rate = 0.0001 if mode == "trend" else -0.0001
        open_interest = 5500.0

    orderbook_service.save(
        session,
        OrderBookSnapshotPayload(
            exchange="binance",
            symbol="BTCUSDT",
            snapshot_time=now,
            best_bid=best_bid,
            best_ask=best_ask,
            bid_depth=bid_depth,
            ask_depth=ask_depth,
            spread=best_ask - best_bid,
            source="fixture",
        ),
    )
    funding_service.save(
        session,
        DerivativesMetricPayload(
            exchange="binance",
            symbol="BTCUSDT",
            metric_time=now,
            metric_type="funding_rate",
            metric_value=funding_rate,
            extra_json={"fundingRate": funding_rate},
            source="fixture",
        ),
    )
    oi_service.save(
        session,
        DerivativesMetricPayload(
            exchange="binance",
            symbol="BTCUSDT",
            metric_time=now,
            metric_type="open_interest",
            metric_value=open_interest,
            extra_json={"openInterestAmount": open_interest},
            source="fixture",
        ),
    )

