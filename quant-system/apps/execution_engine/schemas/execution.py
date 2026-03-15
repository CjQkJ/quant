"""执行输出结构。"""

from __future__ import annotations

from datetime import datetime

from shared.schemas.base import BaseSchema
from shared.schemas.error import ErrorDetail


class PlannedOrder(BaseSchema):
    local_order_id: str
    client_order_id: str
    exchange: str
    symbol: str
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
    side: str
    order_type: str
    price: float
    quantity: float
    status: str


class ExecutionResultOutput(BaseSchema):
    task_id: str
    audit_id: str
    execution_time: datetime
    execution_status: str
    exchange: str
    symbol: str
    orders: list[ExecutionOrderItem]
    execution_summary: str
    error: ErrorDetail | None = None

