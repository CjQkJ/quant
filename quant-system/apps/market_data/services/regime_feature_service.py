"""市场特征聚合服务。"""

from __future__ import annotations

from statistics import pstdev

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.market_data.schemas.feature import MarketFeatureSnapshot
from shared.models.tables import MarketDerivativesMetric, MarketOHLCV, MarketOrderBookSnapshot
from shared.utils.time import ensure_utc, utc_now


class RegimeFeatureService:
    def build_snapshot(self, session: Session, symbol: str, timeframe: str = "5m") -> MarketFeatureSnapshot:
        bars = list(
            reversed(
                list(
                    session.scalars(
                        select(MarketOHLCV)
                        .where(MarketOHLCV.symbol == symbol, MarketOHLCV.timeframe == timeframe)
                        .order_by(MarketOHLCV.open_time.desc())
                        .limit(30)
                    ).all()
                )
            )
        )
        if len(bars) < 2:
            raise ValueError("K 线数据不足，无法构建市场特征")

        latest_bar = bars[-1]
        prev_bar = bars[-2]
        returns = []
        for idx in range(1, len(bars)):
            prev_close = float(bars[idx - 1].close)
            curr_close = float(bars[idx].close)
            returns.append((curr_close - prev_close) / prev_close if prev_close else 0.0)

        orderbook = session.scalar(
            select(MarketOrderBookSnapshot)
            .where(MarketOrderBookSnapshot.symbol == symbol)
            .order_by(MarketOrderBookSnapshot.snapshot_time.desc())
            .limit(1)
        )
        if orderbook is None:
            raise ValueError("盘口快照不足，无法构建市场特征")

        funding = session.scalar(
            select(MarketDerivativesMetric)
            .where(MarketDerivativesMetric.symbol == symbol, MarketDerivativesMetric.metric_type == "funding_rate")
            .order_by(MarketDerivativesMetric.metric_time.desc())
            .limit(1)
        )
        oi = session.scalar(
            select(MarketDerivativesMetric)
            .where(MarketDerivativesMetric.symbol == symbol, MarketDerivativesMetric.metric_type == "open_interest")
            .order_by(MarketDerivativesMetric.metric_time.desc())
            .limit(1)
        )

        best_bid = float(orderbook.best_bid)
        best_ask = float(orderbook.best_ask)
        mid_price = (best_bid + best_ask) / 2 if best_bid and best_ask else float(latest_bar.close)
        top_bid_qty = sum(level["qty"] for level in orderbook.bid_depth_json[:5])
        top_ask_qty = sum(level["qty"] for level in orderbook.ask_depth_json[:5])
        liquidity_score = min((top_bid_qty + top_ask_qty) / 100.0, 1.0)
        spread_bps = ((best_ask - best_bid) / mid_price * 10000) if mid_price else 0.0
        latest_close_time = ensure_utc(latest_bar.close_time)

        return MarketFeatureSnapshot(
            exchange=latest_bar.exchange,
            symbol=latest_bar.symbol,
            timeframe=timeframe,
            as_of=latest_close_time,
            last_price=float(latest_bar.close),
            recent_return=(float(latest_bar.close) - float(prev_bar.close)) / float(prev_bar.close),
            realized_volatility=pstdev(returns) if len(returns) > 1 else abs(returns[0]),
            funding_rate=float(funding.metric_value) if funding else 0.0,
            open_interest=float(oi.metric_value) if oi else 0.0,
            spread_bps=spread_bps,
            liquidity_score=liquidity_score,
            best_bid=best_bid,
            best_ask=best_ask,
            source_freshness_seconds=(utc_now() - latest_close_time).total_seconds(),
        )
