"""paper 执行服务。"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from apps.execution_engine.schemas.execution import ExecutionOrderItem, ExecutionResultOutput, PlannedOrder
from apps.execution_engine.services.account_state_service import AccountStateService
from apps.risk_engine.schemas.risk import AuditDecisionOutput
from apps.risk_engine.services.kill_switch_service import KillSwitchService
from shared.config.settings import get_settings
from shared.models.enums import OrderStatus
from shared.models.tables import ExecutionOrder
from shared.schemas.error import ErrorDetail
from shared.utils.time import utc_now


class OrderExecutor:
    def __init__(
        self,
        account_state_service: AccountStateService,
        kill_switch_service: KillSwitchService,
    ) -> None:
        self.account_state_service = account_state_service
        self.kill_switch_service = kill_switch_service
        self.settings = get_settings()

    def execute(
        self,
        session: Session,
        task_id: str,
        audit: AuditDecisionOutput,
        planned_orders: list[PlannedOrder],
        best_bid: float,
        best_ask: float,
    ) -> ExecutionResultOutput:
        if self.kill_switch_service.is_enabled():
            return ExecutionResultOutput(
                task_id=task_id,
                audit_id=audit.audit_id,
                execution_time=utc_now(),
                execution_status=OrderStatus.SKIPPED,
                exchange="binance",
                symbol="BTCUSDT",
                orders=[],
                execution_summary="kill switch 已启用，执行被拦截",
                error=ErrorDetail(code="KILL_SWITCH", message="kill switch 已启用", retryable=False),
            )

        if not planned_orders:
            return ExecutionResultOutput(
                task_id=task_id,
                audit_id=audit.audit_id,
                execution_time=utc_now(),
                execution_status=OrderStatus.SKIPPED,
                exchange="binance",
                symbol="BTCUSDT",
                orders=[],
                execution_summary="本次审核未允许执行",
            )

        items: list[ExecutionOrderItem] = []
        for planned in planned_orders:
            slippage = self.settings.slippage_bps / 10000
            fill_price = best_ask * (1 + slippage) if planned.side == "buy" else best_bid * (1 - slippage)
            fee = fill_price * planned.quantity * self.settings.taker_fee_bps / 10000
            self.account_state_service.apply_fill(
                symbol=planned.symbol,
                side=planned.side,
                filled_qty=planned.quantity,
                fill_price=fill_price,
                fee=fee,
                slippage_bps=self.settings.slippage_bps,
            )

            row = ExecutionOrder(
                exec_order_id=planned.local_order_id,
                task_id=task_id,
                audit_id=audit.audit_id,
                exchange=planned.exchange,
                symbol=planned.symbol,
                side=planned.side,
                position_side=planned.position_side,
                order_type=planned.order_type,
                execution_mode="paper",
                price=Decimal(str(planned.price)),
                quantity=Decimal(str(planned.quantity)),
                status=OrderStatus.FILLED,
                exchange_order_id=f"paper_{planned.local_order_id}",
                client_order_id=planned.client_order_id,
                avg_fill_price=Decimal(str(fill_price)),
                filled_qty=Decimal(str(planned.quantity)),
                fee=Decimal(str(fee)),
                estimated_slippage_bps=Decimal(str(self.settings.slippage_bps)),
                error_message=None,
                placed_at=utc_now(),
                filled_at=utc_now(),
            )
            session.add(row)
            items.append(
                ExecutionOrderItem(
                    local_order_id=planned.local_order_id,
                    client_order_id=planned.client_order_id,
                    exchange_order_id=row.exchange_order_id,
                    side=planned.side,
                    order_type=planned.order_type,
                    price=fill_price,
                    quantity=planned.quantity,
                    status=OrderStatus.FILLED,
                )
            )

        session.flush()
        return ExecutionResultOutput(
            task_id=task_id,
            audit_id=audit.audit_id,
            execution_time=utc_now(),
            execution_status=OrderStatus.FILLED,
            exchange=planned_orders[0].exchange,
            symbol=planned_orders[0].symbol,
            orders=items,
            execution_summary="paper execution 已完成",
        )

