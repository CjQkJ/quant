"""
加密货币市场分析 CLI 框架：核心多交易所数据聚合模块。
支持 Binance、Bybit、OKX 的 USDT 本位永续合约。
"""

import os
import asyncio
import socket
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import ccxt.async_support as ccxt_async


def _resolve_proxy_url() -> Optional[str]:
    """从环境变量中解析代理地址，未配置时返回 None。"""
    raw_crypto_proxy = os.environ.get("CRYPTO_PROXY")
    if raw_crypto_proxy is not None:
        value = raw_crypto_proxy.strip()
        if not value or value.lower() in {"off", "none", "direct"}:
            return None
        return value

    for key in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        value = (os.environ.get(key) or "").strip()
        if value:
            return value

    for host, port in (("127.0.0.1", 7897), ("127.0.0.1", 7890)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            try:
                sock.connect((host, port))
                return f"http://{host}:{port}"
            except OSError:
                continue

    return None


PROXY_URL = _resolve_proxy_url()


@dataclass
class OrderBook:
    """统一订单簿条目。"""

    price: float
    amount: float
    exchange: str
    side: str  # 'bid' 或 'ask'


@dataclass
class Ticker:
    """聚合行情数据。"""

    symbol: str
    last_price: float
    mark_price: float
    index_price: float
    funding_rate: Optional[float]
    open_interest: Optional[float]
    volume_24h: float


@dataclass
class ExchangeStatus:
    """单个交易所的数据可用性与错误状态。"""

    exchange: str
    symbol: str
    order_book_ok: bool = False
    ticker_ok: bool = False
    order_book_error: Optional[str] = None
    ticker_error: Optional[str] = None


@dataclass
class FetchResult:
    """一次聚合拉取的完整结果。"""

    order_books: Dict[str, Dict[str, List[OrderBook]]]
    tickers: Dict[str, Optional[Ticker]]
    exchange_status: Dict[str, ExchangeStatus]


class FuturesAggregator:
    """
    USDT 本位永续合约多交易所聚合器。
    使用 ccxt.async_support 异步并发拉取数据，提高效率。
    所有异步操作在单次 asyncio.run() 中完成，避免跨事件循环问题。
    """

    def __init__(self, timeout: int = 15000, proxy_url: Optional[str] = None):
        """
        初始化聚合器。

        参数:
            timeout: 请求超时时间（毫秒）
            proxy_url: 显式代理地址，未设置时自动读取环境变量
        """
        self.timeout = timeout
        self.proxy_url = (proxy_url or "").strip() or PROXY_URL

    @staticmethod
    def format_symbol(symbol: str, quote: str = "USDT") -> Dict[str, str]:
        """
        将用户输入的币种符号统一转换为各交易所的永续合约格式。

        参数:
            symbol: 基础币种（如 'btc'、'SOL'、'eth'）
            quote: 计价资产（默认 USDT）

        返回:
            字典，键为交易所名称，值为格式化后的合约符号
        """
        normalized = symbol.upper().strip().replace(" ", "")
        normalized = normalized.replace("-", "/")
        normalized = normalized.split(":")[0]

        if "/" in normalized:
            base = normalized.split("/")[0]
        elif normalized.endswith(quote):
            base = normalized[: -len(quote)]
        else:
            base = normalized

        # 三家交易所统一使用 ccxt 标准永续合约格式
        return {
            "binance": f"{base}/{quote}:{quote}",
            "bybit": f"{base}/{quote}:{quote}",
            "okx": f"{base}/{quote}:{quote}",
        }

    @staticmethod
    def _format_error(exc: Exception) -> str:
        """将异常压缩为单行文本，便于 CLI 展示。"""
        return " ".join(str(exc).split()) or exc.__class__.__name__

    def _build_exchange(self, factory, default_type: str) -> ccxt_async.Exchange:
        """构造单个交易所实例。"""
        config = {
            "enableRateLimit": True,
            "timeout": self.timeout,
            "defaultType": default_type,
            "options": {"defaultType": default_type},
        }
        if self.proxy_url:
            config["httpsProxy"] = self.proxy_url
        return factory(config)

    async def _fetch_single_order_book(
        self,
        name: str,
        exchange: ccxt_async.Exchange,
        symbol: str,
        limit: int,
    ) -> Tuple[str, Dict[str, List[OrderBook]], Optional[str]]:
        """从单个交易所异步拉取订单簿。"""
        try:
            order_book = await exchange.fetch_order_book(symbol, limit)
            bids = [
                OrderBook(price=float(entry[0]), amount=float(entry[1]), exchange=name, side="bid")
                for entry in order_book.get("bids", [])[:limit]
                if len(entry) >= 2
            ]
            asks = [
                OrderBook(price=float(entry[0]), amount=float(entry[1]), exchange=name, side="ask")
                for entry in order_book.get("asks", [])[:limit]
                if len(entry) >= 2
            ]
            error = None if bids and asks else "订单簿为空"
            return name, {"bids": bids, "asks": asks}, error
        except Exception as exc:
            return name, {"bids": [], "asks": []}, self._format_error(exc)

    async def _fetch_single_ticker(
        self,
        name: str,
        exchange: ccxt_async.Exchange,
        symbol: str,
    ) -> Tuple[str, Optional[Ticker], Optional[str]]:
        """从单个交易所异步拉取行情数据。"""
        try:
            ticker = await exchange.fetch_ticker(symbol)

            funding_rate = None
            try:
                if hasattr(exchange, "fetch_funding_rate"):
                    funding_data = await exchange.fetch_funding_rate(symbol)
                    raw_funding = funding_data.get("fundingRate")
                    if raw_funding is not None:
                        funding_rate = float(raw_funding)
            except Exception:
                pass

            open_interest = None
            try:
                oi_data = await exchange.fetch_open_interest(symbol)
                oi_amount = oi_data.get("openInterestAmount")
                oi_value = oi_data.get("openInterestValue")
                last_price = float(ticker.get("last", 0) or 0)
                mark_price = float(ticker.get("markPrice") or 0)
                reference_price = mark_price or last_price

                if oi_value is not None and float(oi_value) > 0 and reference_price > 0:
                    open_interest = float(oi_value) / reference_price
                elif oi_amount is not None and float(oi_amount) > 0:
                    open_interest = float(oi_amount)
            except Exception:
                try:
                    fallback_oi = ticker.get("openInterest")
                    if fallback_oi is not None:
                        open_interest = float(fallback_oi)
                except Exception:
                    pass

            raw_mark_price = ticker.get("markPrice")
            if raw_mark_price is not None:
                mark_price = float(raw_mark_price)
            else:
                mark_price = float(ticker.get("last", 0) or 0)

            result = Ticker(
                symbol=symbol,
                last_price=float(ticker.get("last", 0) or 0),
                mark_price=mark_price,
                index_price=float(ticker.get("indexPrice") or 0),
                funding_rate=funding_rate,
                open_interest=open_interest,
                volume_24h=float(ticker.get("baseVolume") or 0),
            )
            return name, result, None
        except Exception as exc:
            return name, None, self._format_error(exc)

    async def _fetch_all(self, symbol: str, ob_limit: int = 20) -> FetchResult:
        """
        在单个事件循环中并发完成所有数据拉取（订单簿 + 行情），
        并在结束后正确关闭所有交易所连接。
        """
        exchanges = {
            "binance": self._build_exchange(ccxt_async.binance, "future"),
            "bybit": self._build_exchange(ccxt_async.bybit, "linear"),
            "okx": self._build_exchange(ccxt_async.okx, "swap"),
        }
        formatted = self.format_symbol(symbol)
        exchange_status = {
            name: ExchangeStatus(exchange=name, symbol=formatted[name])
            for name in exchanges
        }

        try:
            await asyncio.gather(
                *(exchange.load_markets() for exchange in exchanges.values()),
                return_exceptions=True,
            )

            order_book_results, ticker_results = await asyncio.gather(
                asyncio.gather(
                    *(
                        self._fetch_single_order_book(name, exchange, formatted[name], ob_limit)
                        for name, exchange in exchanges.items()
                    ),
                    return_exceptions=True,
                ),
                asyncio.gather(
                    *(
                        self._fetch_single_ticker(name, exchange, formatted[name])
                        for name, exchange in exchanges.items()
                    ),
                    return_exceptions=True,
                ),
            )

            order_books: Dict[str, Dict[str, List[OrderBook]]] = {}
            for result in order_book_results:
                if isinstance(result, Exception):
                    continue
                name, data, error = result
                order_books[name] = data
                exchange_status[name].order_book_ok = bool(data["bids"] and data["asks"])
                exchange_status[name].order_book_error = error

            tickers: Dict[str, Optional[Ticker]] = {}
            for result in ticker_results:
                if isinstance(result, Exception):
                    continue
                name, data, error = result
                tickers[name] = data
                exchange_status[name].ticker_ok = data is not None
                exchange_status[name].ticker_error = error

            return FetchResult(
                order_books=order_books,
                tickers=tickers,
                exchange_status=exchange_status,
            )
        finally:
            await asyncio.gather(
                *(exchange.close() for exchange in exchanges.values()),
                return_exceptions=True,
            )

    def fetch_all_data(self, symbol: str, ob_limit: int = 20) -> FetchResult:
        """
        一次性拉取所有数据（同步入口）。
        订单簿和行情在同一个事件循环中并发完成。

        参数:
            symbol: 交易标的（如 'BTC'）
            ob_limit: 订单簿深度

        返回:
            FetchResult，包含订单簿、行情与可用性状态
        """
        return asyncio.run(self._fetch_all(symbol, ob_limit))
