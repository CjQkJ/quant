"""
Smart Liquidity Skill 的自带执行入口。
默认输出 JSON，便于 Agent 继续分析。
"""

import argparse
import json

from smart_liquidity import SmartLiquidityAnalyzer


def _serialize_bucket(bucket):
    return {
        "price_range": [bucket.price_range[0], bucket.price_range[1]],
        "asset_amount": bucket.total_ask_amount or bucket.total_bid_amount,
        "notional_usdt": bucket.total_ask_notional or bucket.total_bid_notional,
        "sources": bucket.ask_sources or bucket.bid_sources,
    }


def build_output(result):
    oi_notional = result.oi_total * result.mark_price if result.oi_total > 0 and result.mark_price > 0 else 0.0
    return {
        "symbol": result.symbol,
        "mark_price": result.mark_price,
        "oi_total": result.oi_total,
        "oi_notional": oi_notional,
        "funding_rate_avg": result.funding_rate_avg,
        "sentiment": result.sentiment,
        "top_ask_buckets": [_serialize_bucket(bucket) for bucket in result.top_ask_buckets],
        "top_bid_buckets": [_serialize_bucket(bucket) for bucket in result.top_bid_buckets],
        "order_book_exchanges": result.order_book_exchanges,
        "ticker_exchanges": result.ticker_exchanges,
        "failed_exchanges": result.failed_exchanges,
        "exchange_data": {
            name: {
                "bid_count": data["bid_count"],
                "ask_count": data["ask_count"],
                "order_book_ok": data["order_book_ok"],
                "ticker_ok": data["ticker_ok"],
                "order_book_error": data["order_book_error"],
                "ticker_error": data["ticker_error"],
            }
            for name, data in result.exchange_data.items()
        },
    }


def main():
    parser = argparse.ArgumentParser(description="运行 Smart Liquidity 聚合流动性分析")
    parser.add_argument("--symbol", required=True, help="交易标的，例如 BTC")
    parser.add_argument("--threshold", type=float, default=None, help="参考价格")
    parser.add_argument("--bin-size", type=float, default=100.0, help="价格聚合区间大小")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    analyzer = SmartLiquidityAnalyzer()
    result = analyzer.analyze(
        symbol=args.symbol,
        threshold_price=args.threshold,
        bin_size=args.bin_size,
    )
    payload = build_output(result)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f"标的: {payload['symbol']}")
    print(f"标记价格: {payload['mark_price']:.2f} USDT")
    print(f"全网 OI: {payload['oi_total']:.4f} {payload['symbol']} (~{payload['oi_notional']:.2f} USDT)")
    print(f"平均资金费率: {payload['funding_rate_avg'] * 100:+.4f}%")
    print(f"多空情绪: {payload['sentiment']}")
    print(f"盘口来源: {', '.join(payload['order_book_exchanges']) or '无'}")
    print(f"行情/OI 来源: {', '.join(payload['ticker_exchanges']) or '无'}")


if __name__ == "__main__":
    main()
