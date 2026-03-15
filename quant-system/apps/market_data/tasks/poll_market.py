"""市场轮询任务。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from apps.market_data.clients.binance_rest import BinanceRestClient
from apps.market_data.services.funding_service import FundingService
from apps.market_data.services.ohlcv_service import OHLCVService
from apps.market_data.services.oi_service import OIService
from apps.market_data.services.orderbook_service import OrderBookService
from apps.market_data.services.trades_service import TradesService


class MarketPollTask:
    def __init__(self, client: BinanceRestClient | None = None) -> None:
        self.client = client or BinanceRestClient()
        self.ohlcv_service = OHLCVService()
        self.orderbook_service = OrderBookService()
        self.trades_service = TradesService()
        self.funding_service = FundingService()
        self.oi_service = OIService()

    def run(self, session: Session, symbol: str, timeframe: str = "5m") -> None:
        raw_bars = self.client.fetch_ohlcv(symbol, timeframe=timeframe, limit=200)
        bars = [self.ohlcv_service.normalize("binance", symbol, timeframe, row) for row in raw_bars]
        self.ohlcv_service.save_many(session, bars)

        raw_book = self.client.fetch_order_book(symbol, depth=20)
        orderbook = self.orderbook_service.normalize("binance", symbol, raw_book)
        self.orderbook_service.save(session, orderbook)

        raw_trades = self.client.fetch_trades(symbol, limit=100)
        trades = [self.trades_service.normalize("binance", symbol, row) for row in raw_trades]
        self.trades_service.save_many(session, trades)

        funding = self.funding_service.normalize("binance", symbol, self.client.fetch_funding_rate(symbol))
        self.funding_service.save(session, funding)

        oi = self.oi_service.normalize("binance", symbol, self.client.fetch_open_interest(symbol))
        self.oi_service.save(session, oi)

