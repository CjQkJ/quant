"""Binance WebSocket 配置。"""

from __future__ import annotations


class BinanceStreamSpec:
    base_url = "wss://fstream.binance.com/ws"

    @staticmethod
    def trade_stream(symbol: str) -> str:
        return f"{BinanceStreamSpec.base_url}/{symbol.lower()}@trade"

    @staticmethod
    def depth_stream(symbol: str, levels: int = 20) -> str:
        return f"{BinanceStreamSpec.base_url}/{symbol.lower()}@depth{levels}@100ms"

