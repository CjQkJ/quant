"""
Smart Liquidity Skill：多交易所聚合流动性分析。
包含反幌骗过滤、档位聚合、OI 分析和资金费率情绪判定。
"""

import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

from core.exchange_aggregator import FuturesAggregator, OrderBook


@dataclass
class AggregatedOrderBook:
    """聚合后的订单簿。"""

    bids: List[Tuple[float, float]]  # (价格, 总量)
    asks: List[Tuple[float, float]]  # (价格, 总量)
    mid_price: float


@dataclass
class LiquidityBucket:
    """价格档位的流动性聚合。"""

    price_range: Tuple[float, float]
    total_bid_amount: float
    total_ask_amount: float
    total_bid_notional: float
    total_ask_notional: float
    bid_sources: List[str]
    ask_sources: List[str]


@dataclass
class LiquidityAnalysis:
    """完整的流动性分析结果。"""

    symbol: str
    aggregated_book: AggregatedOrderBook
    top_bid_buckets: List[LiquidityBucket]
    top_ask_buckets: List[LiquidityBucket]
    oi_total: float
    mark_price: float
    funding_rate_avg: float
    sentiment: str  # 'bullish'、'bearish'、'neutral'
    exchange_data: Dict[str, dict]

    @property
    def order_book_exchanges(self) -> List[str]:
        """返回成功提供订单簿的交易所列表。"""
        return [
            name for name, data in self.exchange_data.items()
            if data.get("order_book_ok")
        ]

    @property
    def ticker_exchanges(self) -> List[str]:
        """返回成功提供行情数据的交易所列表。"""
        return [
            name for name, data in self.exchange_data.items()
            if data.get("ticker_ok")
        ]

    @property
    def failed_exchanges(self) -> Dict[str, List[str]]:
        """返回拉取失败的交易所及失败原因。"""
        failures = {}
        for name, data in self.exchange_data.items():
            errors = []
            if data.get("order_book_error"):
                errors.append(f"订单簿: {data['order_book_error']}")
            if data.get("ticker_error"):
                errors.append(f"行情: {data['ticker_error']}")
            if errors:
                failures[name] = errors
        return failures


class SmartLiquiditySkill:
    """
    高精度流动性分析 Skill，具备反幌骗能力。
    聚合 Binance、Bybit、OKX 三家交易所 USDT 本位永续合约数据。
    """

    SPOOF_THRESHOLD_PCT = 0.05

    def __init__(self, aggregator: Optional[FuturesAggregator] = None):
        self.aggregator = aggregator or FuturesAggregator()

    def analyze(
        self,
        symbol: str,
        threshold_price: Optional[float] = None,
        bin_size: float = 100.0,
    ) -> LiquidityAnalysis:
        """
        执行完整的流动性分析。

        参数:
            symbol: 交易标的（如 'BTC'）
            threshold_price: 参考价格，用于反幌骗过滤基准（可选）
            bin_size: 价格聚合区间大小（默认 100 USDT）

        返回:
            LiquidityAnalysis 分析结果
        """
        symbol = symbol.upper().strip()
        if not symbol:
            raise ValueError("交易标的不能为空")
        if bin_size <= 0:
            raise ValueError("价格聚合区间必须大于 0")
        if threshold_price is not None and threshold_price <= 0:
            raise ValueError("参考价格必须大于 0")

        fetch_result = self.aggregator.fetch_all_data(symbol, ob_limit=50)
        order_books = fetch_result.order_books
        tickers = fetch_result.tickers

        filtered_books = self._filter_and_aggregate_books(order_books, threshold_price)

        all_bids = [order for book in filtered_books.values() for order in book["bids"]]
        all_asks = [order for book in filtered_books.values() for order in book["asks"]]
        if not all_bids or not all_asks:
            raise ValueError("交易所订单簿数据不足，无法完成分析")

        best_bid = max(all_bids, key=lambda item: item.price)
        best_ask = min(all_asks, key=lambda item: item.price)
        mid_price = (best_bid.price + best_ask.price) / 2

        aggregated_book = AggregatedOrderBook(
            bids=[(order.price, order.amount) for order in all_bids],
            asks=[(order.price, order.amount) for order in all_asks],
            mid_price=mid_price,
        )

        top_bid_buckets, top_ask_buckets = self._aggregate_into_buckets(
            all_bids,
            all_asks,
            bin_size,
            mid_price,
        )

        oi_total = 0.0
        funding_rates = []
        mark_prices = []
        for ticker in tickers.values():
            if not ticker:
                continue
            if ticker.open_interest is not None:
                oi_total += ticker.open_interest
            if ticker.funding_rate is not None:
                funding_rates.append(ticker.funding_rate)
            if ticker.mark_price > 0:
                mark_prices.append(ticker.mark_price)

        mark_price = sum(mark_prices) / len(mark_prices) if mark_prices else mid_price
        funding_rate_avg = sum(funding_rates) / len(funding_rates) if funding_rates else 0.0

        if funding_rate_avg > 0.0001:
            sentiment = "bullish"
        elif funding_rate_avg < -0.0001:
            sentiment = "bearish"
        else:
            sentiment = "neutral"

        exchange_data = {}
        for exchange_name, status in fetch_result.exchange_status.items():
            book = order_books.get(exchange_name, {"bids": [], "asks": []})
            ticker = tickers.get(exchange_name)
            exchange_data[exchange_name] = {
                "bid_count": len(book["bids"]),
                "ask_count": len(book["asks"]),
                "ticker": ticker,
                "order_book_ok": status.order_book_ok,
                "ticker_ok": status.ticker_ok,
                "order_book_error": status.order_book_error,
                "ticker_error": status.ticker_error,
                "funding_rate_ok": bool(ticker and ticker.funding_rate is not None),
                "open_interest_ok": bool(ticker and ticker.open_interest is not None),
            }

        return LiquidityAnalysis(
            symbol=symbol,
            aggregated_book=aggregated_book,
            top_bid_buckets=top_bid_buckets,
            top_ask_buckets=top_ask_buckets,
            oi_total=oi_total,
            mark_price=mark_price,
            funding_rate_avg=funding_rate_avg,
            sentiment=sentiment,
            exchange_data=exchange_data,
        )

    def _filter_and_aggregate_books(
        self,
        order_books: Dict[str, Dict],
        threshold_price: Optional[float] = None,
    ) -> Dict[str, Dict[str, List[OrderBook]]]:
        """
        反幌骗过滤：移除偏离盘口超过 5% 的异常挂单。
        仅保留参考价格上下 5% 范围内的报价。
        """
        filtered = {}

        for exchange_name, book in order_books.items():
            bids = book.get("bids", [])
            asks = book.get("asks", [])
            if not bids or not asks:
                filtered[exchange_name] = book
                continue

            if threshold_price is not None:
                reference_price = threshold_price
            else:
                best_bid = max(bids, key=lambda item: item.price).price
                best_ask = min(asks, key=lambda item: item.price).price
                reference_price = (best_bid + best_ask) / 2

            lower_bound = reference_price * (1 - self.SPOOF_THRESHOLD_PCT)
            upper_bound = reference_price * (1 + self.SPOOF_THRESHOLD_PCT)

            filtered_bids = [
                bid for bid in bids
                if lower_bound <= bid.price <= reference_price
            ]
            filtered_asks = [
                ask for ask in asks
                if reference_price <= ask.price <= upper_bound
            ]

            filtered[exchange_name] = {
                "bids": filtered_bids,
                "asks": filtered_asks,
            }

        return filtered

    def _aggregate_into_buckets(
        self,
        bids: List[OrderBook],
        asks: List[OrderBook],
        bin_size: float,
        mid_price: float,
    ) -> Tuple[List[LiquidityBucket], List[LiquidityBucket]]:
        """
        将订单簿按价格区间聚合为档位。
        买单聚合中间价以下区间，卖单聚合中间价以上区间。
        """
        bid_buckets = defaultdict(lambda: {"amount": 0.0, "notional": 0.0, "sources": set()})
        ask_buckets = defaultdict(lambda: {"amount": 0.0, "notional": 0.0, "sources": set()})

        for bid in bids:
            if bid.price >= mid_price:
                continue
            bucket_start = math.floor(bid.price / bin_size) * bin_size
            bid_buckets[bucket_start]["amount"] += bid.amount
            bid_buckets[bucket_start]["notional"] += bid.price * bid.amount
            bid_buckets[bucket_start]["sources"].add(bid.exchange)

        for ask in asks:
            if ask.price <= mid_price:
                continue
            bucket_start = math.floor(ask.price / bin_size) * bin_size
            ask_buckets[bucket_start]["amount"] += ask.amount
            ask_buckets[bucket_start]["notional"] += ask.price * ask.amount
            ask_buckets[bucket_start]["sources"].add(ask.exchange)

        top_bids = [
            LiquidityBucket(
                price_range=(bucket_start, bucket_start + bin_size),
                total_bid_amount=data["amount"],
                total_ask_amount=0.0,
                total_bid_notional=data["notional"],
                total_ask_notional=0.0,
                bid_sources=sorted(data["sources"]),
                ask_sources=[],
            )
            for bucket_start, data in sorted(
                bid_buckets.items(),
                key=lambda item: item[1]["notional"],
                reverse=True,
            )[:3]
        ]

        top_asks = [
            LiquidityBucket(
                price_range=(bucket_start, bucket_start + bin_size),
                total_bid_amount=0.0,
                total_ask_amount=data["amount"],
                total_bid_notional=0.0,
                total_ask_notional=data["notional"],
                bid_sources=[],
                ask_sources=sorted(data["sources"]),
            )
            for bucket_start, data in sorted(
                ask_buckets.items(),
                key=lambda item: item[1]["notional"],
                reverse=True,
            )[:3]
        ]

        return top_bids, top_asks

    def close(self):
        """释放资源（连接已在数据拉取后自动关闭）。"""
        pass


def run_analysis(symbol: str, threshold: float = None, bin_size: float = 100.0):
    """便捷函数：执行流动性分析。"""
    skill = SmartLiquiditySkill()
    try:
        return skill.analyze(symbol, threshold, bin_size)
    finally:
        skill.close()


if __name__ == "__main__":
    result = run_analysis("BTC", threshold=84000, bin_size=100)
    print(f"标的: {result.symbol}")
    print(f"标记价格: {result.mark_price}")
    print(f"全网 OI: {result.oi_total}")
    print(f"平均资金费率: {result.funding_rate_avg}")
    print(f"多空情绪: {result.sentiment}")
