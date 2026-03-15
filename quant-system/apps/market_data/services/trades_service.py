"""逐笔成交服务。"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.market_data.schemas.market import TradeTickPayload
from shared.models.tables import MarketTradeTick


class TradesService:
    def normalize(self, exchange: str, symbol: str, raw_trade: dict) -> TradeTickPayload:
        timestamp = raw_trade.get("timestamp") or raw_trade.get("time")
        trade_time = datetime.fromtimestamp(timestamp / 1000, timezone.utc)
        is_buyer_maker = raw_trade.get("info", {}).get("m")
        side = raw_trade.get("side")
        if side is None:
            side = "sell" if is_buyer_maker else "buy"
        return TradeTickPayload(
            exchange=exchange,
            symbol=symbol,
            trade_id=str(raw_trade.get("id")),
            trade_time=trade_time,
            price=float(raw_trade["price"]),
            qty=float(raw_trade["amount"]),
            side=side,
            is_buyer_maker=is_buyer_maker,
            source="binance_rest",
        )

    def save_many(self, session: Session, payloads: list[TradeTickPayload]) -> list[MarketTradeTick]:
        rows: list[MarketTradeTick] = []
        for payload in payloads:
            stmt = select(MarketTradeTick).where(
                MarketTradeTick.exchange == payload.exchange,
                MarketTradeTick.symbol == payload.symbol,
                MarketTradeTick.trade_id == payload.trade_id,
            )
            row = session.scalar(stmt)
            if row is None:
                row = MarketTradeTick(
                    exchange=payload.exchange,
                    symbol=payload.symbol,
                    trade_id=payload.trade_id,
                    trade_time=payload.trade_time,
                    price=Decimal(str(payload.price)),
                    qty=Decimal(str(payload.qty)),
                    side=payload.side,
                    is_buyer_maker=payload.is_buyer_maker,
                    source=payload.source,
                )
                session.add(row)
            rows.append(row)
        session.flush()
        return rows

    def recent(self, session: Session, symbol: str, limit: int = 50) -> list[MarketTradeTick]:
        stmt = (
            select(MarketTradeTick)
            .where(MarketTradeTick.symbol == symbol)
            .order_by(MarketTradeTick.trade_time.desc())
            .limit(limit)
        )
        return list(reversed(list(session.scalars(stmt).all())))
