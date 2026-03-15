"""订单规划服务。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from apps.execution_engine.schemas.execution import PlannedOrder
from apps.execution_engine.services.account_state_service import AccountStateService
from apps.risk_engine.schemas.risk import AuditDecisionOutput
from shared.models.tables import MarketOrderBookSnapshot
from shared.utils.ids import new_execution_id


class OrderPlanner:
    def __init__(self, account_state_service: AccountStateService) -> None:
        self.account_state_service = account_state_service

    def plan(
        self,
        session: Session,
        analysis: AnalysisAgentOutput,
        audit: AuditDecisionOutput,
        orderbook: MarketOrderBookSnapshot,
    ) -> list[PlannedOrder]:
        if not audit.approved:
            return []

        account = self.account_state_service.get()
        equity = float(account["equity"])
        max_position_ratio = float(audit.approved_order_plan.get("max_position_ratio", 0.1))
        side = "sell" if "short" in analysis.directional_bias else "buy"
        price = float(orderbook.best_ask if side == "buy" else orderbook.best_bid)
        quantity = round((equity * max_position_ratio) / price, 6) if price else 0.0
        if quantity <= 0:
            return []

        return [
            PlannedOrder(
                local_order_id=new_execution_id(),
                client_order_id=f"{analysis.symbol.lower()}_{analysis.task_id[-8:]}",
                exchange=analysis.exchange,
                symbol=analysis.symbol,
                side=side,
                position_side="long" if side == "buy" else "short",
                order_type=audit.approved_order_plan.get("entry_mode", "market"),
                price=price,
                quantity=quantity,
            )
        ]

