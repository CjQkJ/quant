"""
crypto-skills-cli：加密货币市场分析命令行框架。
CLI 入口文件。
"""

from typing import List, Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from skills.smart_liquidity import SmartLiquiditySkill


app = typer.Typer(
    name="crypto-skills-cli",
    help="加密货币市场分析命令行工具集",
    rich_markup_mode="rich",
    add_completion=False,
)
console = Console()


@app.command()
def smart_liquidity(
    symbol: str = typer.Option(..., "--symbol", "-s", help="交易标的（如 BTC、ETH、SOL）"),
    threshold: Optional[float] = typer.Option(None, "--threshold", "-t", help="参考价格，用于反幌骗过滤基准（如 84000）"),
    bin_size: float = typer.Option(100.0, "--bin-size", "-b", help="价格聚合区间大小，默认 100 USDT"),
):
    """
    全网聚合流动性分析：聚合 Binance、Bybit、OKX 三家交易所 USDT 本位永续合约深度数据。

    功能：
    - 聚合多交易所真实订单簿深度
    - 反幌骗过滤（剔除异常挂单）
    - 按价格区间展示 Top 3 卖盘/买盘压力
    - 展示全网未平仓量 (OI) 及多空情绪
    """
    symbol = symbol.upper().strip()
    if not symbol:
        raise typer.BadParameter("交易标的不能为空")
    if threshold is not None and threshold <= 0:
        raise typer.BadParameter("参考价格必须大于 0")
    if bin_size <= 0:
        raise typer.BadParameter("价格聚合区间必须大于 0")

    console.print(f"\n[bold cyan]正在拉取 {symbol}/USDT 永续合约数据...[/bold cyan]")

    skill = SmartLiquiditySkill()
    try:
        result = skill.analyze(symbol, threshold, bin_size)
        _display_liquidity_panel(result, symbol)
        _display_oi_panel(result, symbol)
        _display_exchange_summary(result)
    except Exception as exc:
        console.print(f"[bold red]错误:[/bold red] {exc}")
        raise typer.Exit(1)
    finally:
        skill.close()


def _display_liquidity_panel(result, symbol: str):
    """渲染流动性档位面板。"""
    ask_table = Table(
        title=f"[bold]全网聚合 {symbol} 永续合约真实卖盘挂单量 (Top 3 价格区间)[/bold]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    ask_table.add_column("价格区间", style="cyan", justify="center")
    ask_table.add_column(f"卖单总量 ({symbol})", style="red", justify="right")
    ask_table.add_column("卖单名义价值 (USDT)", style="magenta", justify="right")
    ask_table.add_column("数据来源", style="yellow", justify="center")

    for bucket in result.top_ask_buckets:
        ask_table.add_row(
            f"{bucket.price_range[0]:,.2f} - {bucket.price_range[1]:,.2f}",
            f"{bucket.total_ask_amount:,.4f}",
            f"{bucket.total_ask_notional:,.2f}",
            ", ".join(bucket.ask_sources) if bucket.ask_sources else "无",
        )

    if not result.top_ask_buckets:
        ask_table.add_row("--", "--", "--", "--")

    console.print(Panel(ask_table, border_style="red", padding=(0, 1)))

    bid_table = Table(
        title=f"[bold]全网聚合 {symbol} 永续合约真实买盘挂单量 (Top 3 价格区间)[/bold]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    bid_table.add_column("价格区间", style="cyan", justify="center")
    bid_table.add_column(f"买单总量 ({symbol})", style="green", justify="right")
    bid_table.add_column("买单名义价值 (USDT)", style="magenta", justify="right")
    bid_table.add_column("数据来源", style="yellow", justify="center")

    for bucket in result.top_bid_buckets:
        bid_table.add_row(
            f"{bucket.price_range[0]:,.2f} - {bucket.price_range[1]:,.2f}",
            f"{bucket.total_bid_amount:,.4f}",
            f"{bucket.total_bid_notional:,.2f}",
            ", ".join(bucket.bid_sources) if bucket.bid_sources else "无",
        )

    if not result.top_bid_buckets:
        bid_table.add_row("--", "--", "--", "--")

    console.print(Panel(bid_table, border_style="green", padding=(0, 1)))


def _display_oi_panel(result, symbol: str):
    """渲染 OI 与多空情绪面板。"""
    oi_base = result.oi_total
    oi_value = oi_base * result.mark_price if result.mark_price > 0 and oi_base > 0 else 0
    oi_value_millions = oi_value / 1_000_000 if oi_value > 0 else 0
    funding_pct = result.funding_rate_avg * 100

    sentiment_map = {
        "bullish": ("green", "看多 (BULLISH)"),
        "bearish": ("red", "看空 (BEARISH)"),
        "neutral": ("yellow", "中性 (NEUTRAL)"),
    }
    sentiment_color, sentiment_text = sentiment_map.get(result.sentiment, ("white", result.sentiment))

    info_table = Table(
        title=f"[bold]{symbol} 合约持仓量 (OI) 状态与多空情绪[/bold]",
        box=box.ROUNDED,
        show_header=False,
    )
    info_table.add_column("指标", style="cyan", justify="left")
    info_table.add_column("数值", style="white", justify="right")
    info_table.add_row("当前标记价格", f"[bold]{result.mark_price:,.2f} USDT[/bold]")
    info_table.add_row("全网未平仓量 (OI)", f"[bold]{oi_base:,.4f} {symbol} (~{oi_value_millions:,.0f}M USDT)[/bold]")
    info_table.add_row("平均资金费率", f"[bold]{funding_pct:+.4f}%[/bold]")
    info_table.add_row("多空情绪", f"[bold {sentiment_color}]{sentiment_text}[/bold {sentiment_color}]")

    if result.sentiment == "bullish":
        explanation = "资金费率为正，多头持仓占优，市场偏多"
    elif result.sentiment == "bearish":
        explanation = "资金费率为负，空头持仓占优，市场偏空"
    else:
        explanation = "资金费率接近零，多空平衡"

    console.print(Panel(info_table, border_style="blue", padding=(0, 1)))
    console.print(f"[dim]解读: {explanation}[/dim]")


def _format_exchange_names(exchanges: List[str]) -> str:
    """格式化交易所列表。"""
    alias = {
        "binance": "Binance",
        "bybit": "Bybit",
        "okx": "OKX",
    }
    names = [alias.get(exchange, exchange) for exchange in exchanges]
    return ", ".join(names) if names else "无"


def _display_exchange_summary(result):
    """渲染交易所可用性与降级提示。"""
    console.print(f"\n[dim]盘口数据来源: {_format_exchange_names(result.order_book_exchanges)}[/dim]")
    console.print(f"[dim]行情/OI 数据来源: {_format_exchange_names(result.ticker_exchanges)}[/dim]")

    if not result.failed_exchanges:
        return

    warning_lines = [
        f"{_format_exchange_names([exchange])}: {'；'.join(errors)}"
        for exchange, errors in result.failed_exchanges.items()
    ]
    console.print(Panel(
        "\n".join(warning_lines),
        title="交易所降级",
        border_style="yellow",
        padding=(0, 1),
    ))


@app.command()
def version():
    """显示版本信息。"""
    console.print("[bold cyan]crypto-skills-cli[/bold cyan] v0.1.0")
    console.print("加密货币市场分析命令行工具集")


if __name__ == "__main__":
    app()
