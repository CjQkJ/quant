# Smart Liquidity 输出契约

`run_analysis.py --json` 输出一个 JSON 对象，核心字段如下：

```json
{
  "symbol": "BTC",
  "mark_price": 71557.97,
  "oi_total": 158976.9897,
  "oi_notional": 11376000000.0,
  "funding_rate_avg": -0.000044,
  "sentiment": "neutral",
  "top_ask_buckets": [
    {
      "price_range": [71500.0, 71600.0],
      "asset_amount": 591.346,
      "notional_usdt": 42322625.1,
      "sources": ["bybit", "okx"]
    }
  ],
  "top_bid_buckets": [],
  "order_book_exchanges": ["binance", "bybit", "okx"],
  "ticker_exchanges": ["binance", "bybit", "okx"],
  "failed_exchanges": {}
}
```

## 字段解释

- `top_ask_buckets[].asset_amount` / `top_bid_buckets[].asset_amount`：基础资产数量
- `top_ask_buckets[].notional_usdt` / `top_bid_buckets[].notional_usdt`：USDT 名义价值
- `order_book_exchanges`：成功提供盘口数据的交易所
- `ticker_exchanges`：成功提供行情 / Funding / OI 的交易所
- `failed_exchanges`：失败交易所及原因数组

## 输出使用要求

- 汇报给用户时，数量和名义价值要分开写
- 若 `failed_exchanges` 非空，必须显式告知降级
- 若 `top_ask_buckets` 或 `top_bid_buckets` 为空，不要自行脑补压力位
