import unittest

from core.exchange_aggregator import (
    ExchangeStatus,
    FetchResult,
    FuturesAggregator,
    OrderBook,
    Ticker,
)
from skills.smart_liquidity import SmartLiquiditySkill


class StubAggregator:
    def __init__(self, fetch_result: FetchResult):
        self.fetch_result = fetch_result

    def fetch_all_data(self, symbol: str, ob_limit: int = 20) -> FetchResult:
        return self.fetch_result


class SmartLiquiditySkillTestCase(unittest.TestCase):
    def test_format_symbol_normalizes_spot_like_inputs(self):
        formatted = FuturesAggregator.format_symbol(" btc / usdt ")
        self.assertEqual(formatted["binance"], "BTC/USDT:USDT")
        self.assertEqual(formatted["bybit"], "BTC/USDT:USDT")
        self.assertEqual(formatted["okx"], "BTC/USDT:USDT")

    def test_analyze_rejects_invalid_bin_size(self):
        skill = SmartLiquiditySkill(aggregator=StubAggregator(self._build_fetch_result()))
        with self.assertRaisesRegex(ValueError, "价格聚合区间必须大于 0"):
            skill.analyze("BTC", bin_size=0)

    def test_spoof_filter_uses_five_percent_window(self):
        skill = SmartLiquiditySkill(aggregator=StubAggregator(self._build_fetch_result()))
        order_books = {
            "bybit": {
                "bids": [
                    OrderBook(price=100.0, amount=1.0, exchange="bybit", side="bid"),
                    OrderBook(price=92.0, amount=5.0, exchange="bybit", side="bid"),
                ],
                "asks": [
                    OrderBook(price=101.0, amount=1.0, exchange="bybit", side="ask"),
                    OrderBook(price=108.0, amount=5.0, exchange="bybit", side="ask"),
                ],
            }
        }

        filtered = skill._filter_and_aggregate_books(order_books, threshold_price=100.0)
        self.assertEqual(len(filtered["bybit"]["bids"]), 1)
        self.assertEqual(len(filtered["bybit"]["asks"]), 1)

    def test_analyze_tracks_notional_and_exchange_failures(self):
        skill = SmartLiquiditySkill(aggregator=StubAggregator(self._build_fetch_result()))
        result = skill.analyze("BTC", bin_size=2.5)

        self.assertEqual(result.order_book_exchanges, ["bybit", "okx"])
        self.assertEqual(result.ticker_exchanges, ["bybit", "okx"])
        self.assertIn("binance", result.failed_exchanges)

        top_ask = result.top_ask_buckets[0]
        self.assertEqual(top_ask.price_range, (102.5, 105.0))
        self.assertAlmostEqual(top_ask.total_ask_amount, 4.0)
        self.assertAlmostEqual(top_ask.total_ask_notional, 413.5)
        self.assertEqual(top_ask.ask_sources, ["bybit", "okx"])

        top_bid = result.top_bid_buckets[0]
        self.assertEqual(top_bid.price_range, (97.5, 100.0))
        self.assertAlmostEqual(top_bid.total_bid_amount, 7.0)
        self.assertAlmostEqual(top_bid.total_bid_notional, 688.0)
        self.assertEqual(top_bid.bid_sources, ["bybit", "okx"])

    @staticmethod
    def _build_fetch_result() -> FetchResult:
        order_books = {
            "binance": {"bids": [], "asks": []},
            "bybit": {
                "bids": [
                    OrderBook(price=99.0, amount=3.0, exchange="bybit", side="bid"),
                    OrderBook(price=98.0, amount=2.0, exchange="bybit", side="bid"),
                ],
                "asks": [
                    OrderBook(price=101.0, amount=1.0, exchange="bybit", side="ask"),
                    OrderBook(price=103.0, amount=3.0, exchange="bybit", side="ask"),
                ],
            },
            "okx": {
                "bids": [
                    OrderBook(price=97.5, amount=2.0, exchange="okx", side="bid"),
                ],
                "asks": [
                    OrderBook(price=104.5, amount=1.0, exchange="okx", side="ask"),
                ],
            },
        }
        tickers = {
            "binance": None,
            "bybit": Ticker(
                symbol="BTC/USDT:USDT",
                last_price=100.0,
                mark_price=100.0,
                index_price=100.0,
                funding_rate=0.0002,
                open_interest=10.0,
                volume_24h=1_000.0,
            ),
            "okx": Ticker(
                symbol="BTC/USDT:USDT",
                last_price=100.0,
                mark_price=102.0,
                index_price=101.0,
                funding_rate=-0.0001,
                open_interest=5.0,
                volume_24h=800.0,
            ),
        }
        exchange_status = {
            "binance": ExchangeStatus(
                exchange="binance",
                symbol="BTC/USDT:USDT",
                order_book_ok=False,
                ticker_ok=False,
                order_book_error="418 banned",
                ticker_error="418 banned",
            ),
            "bybit": ExchangeStatus(
                exchange="bybit",
                symbol="BTC/USDT:USDT",
                order_book_ok=True,
                ticker_ok=True,
            ),
            "okx": ExchangeStatus(
                exchange="okx",
                symbol="BTC/USDT:USDT",
                order_book_ok=True,
                ticker_ok=True,
            ),
        }
        return FetchResult(
            order_books=order_books,
            tickers=tickers,
            exchange_status=exchange_status,
        )


if __name__ == "__main__":
    unittest.main()
