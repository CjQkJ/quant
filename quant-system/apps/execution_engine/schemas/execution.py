"""执行输出结构。"""

from __future__ import annotations

from datetime import datetime

from shared.schemas.base import BaseSchema
from shared.schemas.error import ErrorDetail


class PositionSnapshot(BaseSchema):
    symbol: str
    qty: float
    side: str
    avg_entry_price: float
    mark_price: float
    notional: float
    realized_pnl: float
    unrealized_pnl: float


class PaperAccountSnapshot(BaseSchema):
    snapshot_id: str
    account_mode: str
    market_type: str
    equity: float
    cash_balance: float
    available_balance: float
    used_margin: float
    realized_pnl: float
    unrealized_pnl: float
    avg_slippage_bps: float
    positions: list[PositionSnapshot]
    updated_at: datetime


class PlannedOrder(BaseSchema):
    local_order_id: str
    client_order_id: str
    exchange: str
    symbol: str
    market_type: str
    account_mode: str
    side: str
    position_side: str
    order_type: str
    price: float
    quantity: float
    execution_mode: str = "paper"


class ExecutionOrderItem(BaseSchema):
    local_order_id: str
    client_order_id: str
    exchange_order_id: str | None = None
    market_type: str
    account_mode: str
    side: str
    order_type: str
    price: float
    quantity: float
    status: str
    realized_pnl: float = 0.0
    unrealized_pnl_at_fill: float = 0.0


class ExecutionResultOutput(BaseSchema):
    task_id: str
    audit_id: str
    strategy_signal_id: str | None = None
    execution_time: datetime
    execution_status: str
    exchange: str
    symbol: str
    market_type: str
    account_mode: str
    orders: list[ExecutionOrderItem]
    account_snapshot: PaperAccountSnapshot
    execution_summary: str
    error: ErrorDetail | None = None
