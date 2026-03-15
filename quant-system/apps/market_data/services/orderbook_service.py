"""盘口快照服务。"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.market_data.schemas.market import OrderBookSnapshotPayload, OrderLevel
from shared.models.tables import MarketOrderBookSnapshot


class OrderBookService:
    def normalize(self, exchange: str, symbol: str, raw_book: dict) -> OrderBookSnapshotPayload:
        bids = [OrderLevel(price=float(price), qty=float(qty)) for price, qty in raw_book.get("bids", [])]
        asks = [OrderLevel(price=float(price), qty=float(qty)) for price, qty in raw_book.get("asks", [])]
        best_bid = bids[0].price if bids else 0.0
        best_ask = asks[0].price if asks else 0.0
        spread = max(best_ask - best_bid, 0.0)
        ts = raw_book.get("timestamp")
        snapshot_time = datetime.fromtimestamp((ts or int(datetime.now(timezone.utc).timestamp() * 1000)) / 1000, timezone.utc)
        return OrderBookSnapshotPayload(
            exchange=exchange,
            symbol=symbol,
            snapshot_time=snapshot_time,
            best_bid=best_bid,
            best_ask=best_ask,
            bid_depth=bids,
            ask_depth=asks,
            spread=spread,
            source="binance_rest",
        )

    def save(self, session: Session, payload: OrderBookSnapshotPayload) -> MarketOrderBookSnapshot:
        row = MarketOrderBookSnapshot(
            exchange=payload.exchange,
            symbol=payload.symbol,
            snapshot_time=payload.snapshot_time,
            best_bid=Decimal(str(payload.best_bid)),
            best_ask=Decimal(str(payload.best_ask)),
            bid_depth_json=[level.model_dump() for level in payload.bid_depth],
            ask_depth_json=[level.model_dump() for level in payload.ask_depth],
            spread=Decimal(str(payload.spread)),
            source=payload.source,
        )
        session.add(row)
        session.flush()
        return row

    def latest(self, session: Session, symbol: str) -> MarketOrderBookSnapshot | None:
        stmt = (
            select(MarketOrderBookSnapshot)
            .where(MarketOrderBookSnapshot.symbol == symbol)
            .order_by(MarketOrderBookSnapshot.snapshot_time.desc())
            .limit(1)
        )
        return session.scalar(stmt)
