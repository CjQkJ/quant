from __future__ import annotations

from apps.market_data.services.ohlcv_service import OHLCVService
from apps.market_data.services.orderbook_service import OrderBookService


def test_ohlcv_normalize_and_upsert(session):
    service = OHLCVService()
    payload = service.normalize("binance", "BTCUSDT", "5m", [1_700_000_000_000, "1", "2", "0.5", "1.5", "100", None, None, 10])
    service.save_many(session, [payload])
    service.save_many(session, [payload])
    rows = service.get_recent(session, "BTCUSDT", "5m")
    assert len(rows) == 1
    assert float(rows[0].close) == 1.5


def test_orderbook_normalize(session):
    service = OrderBookService()
    payload = service.normalize(
        "binance",
        "BTCUSDT",
        {"timestamp": 1_700_000_000_000, "bids": [[100.0, 2.0]], "asks": [[100.5, 1.5]]},
    )
    row = service.save(session, payload)
    assert float(row.best_bid) == 100.0
    assert float(row.best_ask) == 100.5
    assert float(row.spread) == 0.5

