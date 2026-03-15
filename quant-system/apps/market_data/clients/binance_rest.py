"""Binance REST 客户端。"""

from __future__ import annotations

from typing import Any

import ccxt

from shared.config.settings import get_settings


def format_binance_symbol(symbol: str) -> str:
    symbol = symbol.upper().strip()
    if symbol.endswith("USDT") and "/" not in symbol:
        base = symbol[:-4]
    elif "/" in symbol:
        base = symbol.split("/")[0]
    else:
        base = symbol
    return f"{base}/USDT:USDT"


class BinanceRestClient:
    """第一阶段只连接 Binance 永续。"""

    def __init__(self, proxy_url: str | None = None) -> None:
        settings = get_settings()
        config: dict[str, Any] = {
            "enableRateLimit": True,
            "options": {"defaultType": "future"},
        }
        proxy = proxy_url if proxy_url is not None else settings.binance_proxy
        if proxy:
            config["httpsProxy"] = proxy
        self.exchange = ccxt.binance(config)

    def fetch_ohlcv(self, symbol: str, timeframe: str = "5m", limit: int = 200) -> list[list[Any]]:
        return self.exchange.fetch_ohlcv(format_binance_symbol(symbol), timeframe=timeframe, limit=limit)

    def fetch_order_book(self, symbol: str, depth: int = 20) -> dict[str, Any]:
        return self.exchange.fetch_order_book(format_binance_symbol(symbol), limit=depth)

    def fetch_trades(self, symbol: str, limit: int = 100) -> list[dict[str, Any]]:
        return self.exchange.fetch_trades(format_binance_symbol(symbol), limit=limit)

    def fetch_funding_rate(self, symbol: str) -> dict[str, Any]:
        return self.exchange.fetch_funding_rate(format_binance_symbol(symbol))

    def fetch_open_interest(self, symbol: str) -> dict[str, Any]:
        return self.exchange.fetch_open_interest(format_binance_symbol(symbol))

    def close(self) -> None:
        try:
            self.exchange.close()
        except Exception:
            return

