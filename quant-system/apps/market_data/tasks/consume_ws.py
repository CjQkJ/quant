"""WS 消费骨架。"""

from __future__ import annotations

import json

import websockets

from apps.market_data.clients.binance_ws import BinanceStreamSpec


async def consume_trade_stream(symbol: str):
    async with websockets.connect(BinanceStreamSpec.trade_stream(symbol)) as websocket:
        while True:
            yield json.loads(await websocket.recv())


async def consume_depth_stream(symbol: str, levels: int = 20):
    async with websockets.connect(BinanceStreamSpec.depth_stream(symbol, levels=levels)) as websocket:
        while True:
            yield json.loads(await websocket.recv())

