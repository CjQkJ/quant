"""订单规划服务。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from apps.execution_engine.schemas.execution import PlannedOrder
from apps.execution_engine.services.account_state_service import AccountStateService
from apps.risk_engine.schemas.risk import AuditDecisionOutput
from apps.strategy_runtime.schemas.signal import StrategySignal
from shared.models.tables import MarketOrderBookSnapshot
from shared.config.settings import get_settings
from shared.utils.ids import new_execution_id


class OrderPlanner:
    def __init__(self, account_state_service: AccountStateService) -> None:
        self.account_state_service = account_state_service
        self.settings = get_settings()

    def plan(
        self,
        session: Session,
        analysis: AnalysisAgentOutput,
        audit: AuditDecisionOutput,
        strategy_signal: StrategySignal,
        orderbook: MarketOrderBookSnapshot,
    ) -> list[PlannedOrder]:
        if not audit.approved:
            return []

        account = self.account_state_service.get()
        equity = float(account["equity"])
        position = self.account_state_service.get_position(analysis.symbol)
        current_qty = float(position.get("qty", 0.0))
        mid_price = float((orderbook.best_ask + orderbook.best_bid) / 2) if orderbook.best_ask and orderbook.best_bid else float(orderbook.best_ask or orderbook.best_bid or 0.0)
        if mid_price <= 0:
            return []

        max_position_ratio = float(audit.approved_order_plan.get("max_position_ratio", 0.1))
        desired_qty = current_qty

        if strategy_signal.action == "entry":
            target_ratio = min(float(strategy_signal.target_position_ratio), max_position_ratio)
            target_notional = equity * target_ratio
            target_qty = target_notional / mid_price if mid_price else 0.0
            desired_qty = target_qty if strategy_signal.direction == "long" else -target_qty
        elif strategy_signal.action == "reduce":
            if abs(current_qty) < 1e-9:
                return []
            target_ratio = min(float(strategy_signal.target_position_ratio), abs(current_qty * mid_price) / equity if equity else 0.0)
            target_notional = equity * target_ratio
            target_qty = target_notional / mid_price if mid_price else 0.0
            desired_qty = target_qty if current_qty > 0 else -target_qty
        elif strategy_signal.action == "exit":
            desired_qty = 0.0
        else:
            return []

        delta_qty = desired_qty - current_qty
        quantity = round(abs(delta_qty), 6)
        if quantity <= 0:
            return []

        side = "buy" if delta_qty > 0 else "sell"
        position_side = position.get("side", "flat")
        if strategy_signal.action == "entry":
            position_side = strategy_signal.direction
        price = float(orderbook.best_ask if side == "buy" else orderbook.best_bid)
        if price <= 0:
            return []

        return [
            PlannedOrder(
                local_order_id=new_execution_id(),
                client_order_id=f"{analysis.symbol.lower()}_{analysis.task_id[-8:]}",
                exchange=analysis.exchange,
                symbol=analysis.symbol,
                market_type=self.settings.default_market_type,
                account_mode=self.settings.default_account_mode,
                side=side,
                position_side=position_side if position_side != "flat" else ("long" if side == "buy" else "short"),
                order_type="market" if strategy_signal.action in {"reduce", "exit"} else audit.approved_order_plan.get("entry_mode", "market"),
                price=price,
                quantity=quantity,
            )
        ]
