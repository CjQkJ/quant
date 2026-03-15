"""K 线服务。"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.market_data.schemas.market import OHLCVPayload
from shared.models.tables import MarketOHLCV


class OHLCVService:
    def normalize(self, exchange: str, symbol: str, timeframe: str, raw_entry: list) -> OHLCVPayload:
        open_time = datetime.fromtimestamp(raw_entry[0] / 1000, timezone.utc)
        close_time = datetime.fromtimestamp((raw_entry[0] / 1000) + 300, timezone.utc)
        close = float(raw_entry[4])
        volume = float(raw_entry[5])
        return OHLCVPayload(
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe,
            open_time=open_time,
            close_time=close_time,
            open=float(raw_entry[1]),
            high=float(raw_entry[2]),
            low=float(raw_entry[3]),
            close=close,
            volume=volume,
            quote_volume=close * volume,
            trade_count=int(raw_entry[8]) if len(raw_entry) > 8 and raw_entry[8] is not None else None,
            source="binance_rest",
        )

    def save_many(self, session: Session, payloads: list[OHLCVPayload]) -> list[MarketOHLCV]:
        rows: list[MarketOHLCV] = []
        for payload in payloads:
            stmt = select(MarketOHLCV).where(
                MarketOHLCV.exchange == payload.exchange,
                MarketOHLCV.symbol == payload.symbol,
                MarketOHLCV.timeframe == payload.timeframe,
                MarketOHLCV.open_time == payload.open_time,
            )
            row = session.scalar(stmt)
            if row is None:
                row = MarketOHLCV(
                    exchange=payload.exchange,
                    symbol=payload.symbol,
                    timeframe=payload.timeframe,
                    open_time=payload.open_time,
                    close_time=payload.close_time,
                    open=Decimal(str(payload.open)),
                    high=Decimal(str(payload.high)),
                    low=Decimal(str(payload.low)),
                    close=Decimal(str(payload.close)),
                    volume=Decimal(str(payload.volume)),
                    quote_volume=Decimal(str(payload.quote_volume)),
                    trade_count=payload.trade_count,
                    source=payload.source,
                )
                session.add(row)
            else:
                row.close_time = payload.close_time
                row.open = Decimal(str(payload.open))
                row.high = Decimal(str(payload.high))
                row.low = Decimal(str(payload.low))
                row.close = Decimal(str(payload.close))
                row.volume = Decimal(str(payload.volume))
                row.quote_volume = Decimal(str(payload.quote_volume))
                row.trade_count = payload.trade_count
                row.source = payload.source
            rows.append(row)
        session.flush()
        return rows

    def get_recent(self, session: Session, symbol: str, timeframe: str, limit: int = 50) -> list[MarketOHLCV]:
        stmt = (
            select(MarketOHLCV)
            .where(MarketOHLCV.symbol == symbol, MarketOHLCV.timeframe == timeframe)
            .order_by(MarketOHLCV.open_time.desc())
            .limit(limit)
        )
        return list(reversed(list(session.scalars(stmt).all())))
