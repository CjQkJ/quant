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
        strategy_signal_id: str | None = None,
        symbol: str = "BTCUSDT",
        exchange: str = "binance",
    ) -> ExecutionResultOutput:
        account_snapshot = self.account_state_service.persist_snapshot(session, task_id=task_id, symbol=symbol)
        if self.kill_switch_service.is_enabled():
            return ExecutionResultOutput(
                task_id=task_id,
                audit_id=audit.audit_id,
                strategy_signal_id=strategy_signal_id,
                execution_time=utc_now(),
                execution_status=OrderStatus.SKIPPED,
                exchange=exchange,
                symbol=symbol,
                market_type=self.settings.default_market_type,
                account_mode=self.settings.default_account_mode,
                orders=[],
                account_snapshot=account_snapshot,
                execution_summary="kill switch 已启用，执行被拦截",
                error=ErrorDetail(code="KILL_SWITCH", message="kill switch 已启用", retryable=False),
            )

        if not planned_orders:
            return ExecutionResultOutput(
                task_id=task_id,
                audit_id=audit.audit_id,
                strategy_signal_id=strategy_signal_id,
                execution_time=utc_now(),
                execution_status=OrderStatus.SKIPPED,
                exchange=exchange,
                symbol=symbol,
                market_type=self.settings.default_market_type,
                account_mode=self.settings.default_account_mode,
                orders=[],
                account_snapshot=account_snapshot,
                execution_summary="本次审核未允许执行",
            )

        items: list[ExecutionOrderItem] = []
        for planned in planned_orders:
            slippage = self.settings.slippage_bps / 10000
            fill_price = best_ask * (1 + slippage) if planned.side == "buy" else best_bid * (1 - slippage)
            fee = fill_price * planned.quantity * self.settings.taker_fee_bps / 10000
            execution_latency_ms = 25.0
            state = self.account_state_service.apply_fill(
                symbol=planned.symbol,
                side=planned.side,
                filled_qty=planned.quantity,
                fill_price=fill_price,
                fee=fee,
                slippage_bps=self.settings.slippage_bps,
                execution_latency_ms=execution_latency_ms,
            )
            self.account_state_service.mark_to_market(planned.symbol, fill_price)
            position = state.get("positions", {}).get(planned.symbol, {})

            row = ExecutionOrder(
                exec_order_id=planned.local_order_id,
                task_id=task_id,
                audit_id=audit.audit_id,
                strategy_signal_id=strategy_signal_id,
                exchange=planned.exchange,
                symbol=planned.symbol,
                market_type=planned.market_type,
                account_mode=planned.account_mode,
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
                realized_pnl=Decimal(str(position.get("realized_pnl", 0.0))),
                unrealized_pnl_at_fill=Decimal(str(position.get("unrealized_pnl", 0.0))),
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
                    market_type=planned.market_type,
                    account_mode=planned.account_mode,
                    side=planned.side,
                    order_type=planned.order_type,
                    price=fill_price,
                    quantity=planned.quantity,
                    status=OrderStatus.FILLED,
                    realized_pnl=float(position.get("realized_pnl", 0.0)),
                    unrealized_pnl_at_fill=float(position.get("unrealized_pnl", 0.0)),
                )
            )

        session.flush()
        account_snapshot = self.account_state_service.persist_snapshot(session, task_id=task_id, symbol=planned_orders[0].symbol)
        return ExecutionResultOutput(
            task_id=task_id,
            audit_id=audit.audit_id,
            strategy_signal_id=strategy_signal_id,
            execution_time=utc_now(),
            execution_status=OrderStatus.FILLED,
            exchange=planned_orders[0].exchange,
            symbol=planned_orders[0].symbol,
            market_type=planned_orders[0].market_type,
            account_mode=planned_orders[0].account_mode,
            orders=items,
            account_snapshot=account_snapshot,
            execution_summary="paper execution 已完成",
        )
