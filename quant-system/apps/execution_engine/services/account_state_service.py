"""paper 账户状态服务。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from apps.execution_engine.schemas.execution import PaperAccountSnapshot, PositionSnapshot
from shared.config.settings import get_settings
from shared.models.tables import PaperAccountSnapshot as PaperAccountSnapshotRow
from shared.utils.ids import new_snapshot_id
from shared.utils.state_store import StateStore
from shared.utils.time import ensure_utc, utc_now


class AccountStateService:
    ACCOUNT_KEY = "paper:account"

    def __init__(self, state_store: StateStore) -> None:
        self.state_store = state_store
        self.settings = get_settings()

    def _default_state(self) -> dict:
        return {
            "mode": "paper",
            "account_mode": self.settings.default_account_mode,
            "market_type": self.settings.default_market_type,
            "cash_balance": self.settings.paper_initial_equity,
            "equity": self.settings.paper_initial_equity,
            "available_balance": self.settings.paper_initial_equity,
            "used_margin": 0.0,
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
            "fee_paid_total": 0.0,
            "peak_equity": self.settings.paper_initial_equity,
            "consecutive_loss_count": 0,
            "avg_slippage_bps": 0.0,
            "last_execution_latency_ms": 0.0,
            "positions": {},
            "updated_at": utc_now().isoformat(),
        }

    def get(self) -> dict:
        state = self.state_store.get_json(self.ACCOUNT_KEY, self._default_state())
        return self._recalculate_state(state)

    def save(self, state: dict) -> None:
        state = self._recalculate_state(state)
        state["updated_at"] = utc_now().isoformat()
        self.state_store.set_json(self.ACCOUNT_KEY, state)

    def get_position(self, symbol: str) -> dict:
        state = self.get()
        return state.get("positions", {}).get(symbol, self._empty_position())

    def _empty_position(self) -> dict:
        return {
            "qty": 0.0,
            "side": "flat",
            "avg_entry_price": 0.0,
            "mark_price": 0.0,
            "notional": 0.0,
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
        }

    def _recalculate_state(self, state: dict) -> dict:
        positions = state.setdefault("positions", {})
        total_unrealized = 0.0
        total_margin = 0.0

        for symbol, position in list(positions.items()):
            qty = float(position.get("qty", 0.0))
            mark_price = float(position.get("mark_price", position.get("avg_entry_price", 0.0)))
            avg_entry_price = float(position.get("avg_entry_price", 0.0))

            if abs(qty) < 1e-9:
                positions[symbol] = self._empty_position()
                continue

            if qty > 0:
                unrealized = (mark_price - avg_entry_price) * qty
                side = "long"
            else:
                unrealized = (avg_entry_price - mark_price) * abs(qty)
                side = "short"

            notional = abs(qty * mark_price)
            positions[symbol] = {
                "qty": qty,
                "side": side,
                "avg_entry_price": avg_entry_price,
                "mark_price": mark_price,
                "notional": notional,
                "realized_pnl": float(position.get("realized_pnl", 0.0)),
                "unrealized_pnl": unrealized,
            }
            total_unrealized += unrealized
            total_margin += notional * self.settings.paper_initial_margin_ratio

        cash_balance = float(state.get("cash_balance", self.settings.paper_initial_equity))
        equity = cash_balance + total_unrealized
        state["unrealized_pnl"] = total_unrealized
        state["used_margin"] = total_margin
        state["equity"] = equity
        state["available_balance"] = max(0.0, equity - total_margin)
        state["peak_equity"] = max(float(state.get("peak_equity", equity)), equity)
        return state

    def mark_to_market(self, symbol: str, mark_price: float) -> dict:
        state = self.get()
        position = state.setdefault("positions", {}).get(symbol, self._empty_position())
        if abs(float(position.get("qty", 0.0))) >= 1e-9:
            position["mark_price"] = mark_price
            state["positions"][symbol] = position
        self.save(state)
        return state

    def apply_fill(
        self,
        *,
        symbol: str,
        side: str,
        filled_qty: float,
        fill_price: float,
        fee: float,
        slippage_bps: float,
        execution_latency_ms: float = 0.0,
    ) -> dict:
        state = self.get()
        positions = state.setdefault("positions", {})
        current = positions.get(symbol, self._empty_position())
        current_qty = float(current.get("qty", 0.0))
        avg_entry_price = float(current.get("avg_entry_price", 0.0))
        fill_signed_qty = filled_qty if side == "buy" else -filled_qty
        resulting_qty = current_qty + fill_signed_qty
        realized_delta = 0.0

        if abs(current_qty) < 1e-9 or current_qty * fill_signed_qty > 0:
            total_cost = abs(current_qty) * avg_entry_price + abs(fill_signed_qty) * fill_price
            total_qty = abs(current_qty) + abs(fill_signed_qty)
            new_avg_entry = total_cost / total_qty if total_qty else 0.0
        else:
            close_qty = min(abs(current_qty), abs(fill_signed_qty))
            if current_qty > 0:
                realized_delta = (fill_price - avg_entry_price) * close_qty
            else:
                realized_delta = (avg_entry_price - fill_price) * close_qty

            if abs(resulting_qty) < 1e-9:
                new_avg_entry = 0.0
            elif current_qty * resulting_qty > 0:
                new_avg_entry = avg_entry_price
            else:
                new_avg_entry = fill_price

        fee_paid_total = float(state.get("fee_paid_total", 0.0)) + fee
        state["fee_paid_total"] = fee_paid_total
        state["cash_balance"] = float(state.get("cash_balance", self.settings.paper_initial_equity)) + realized_delta - fee
        state["realized_pnl"] = float(state.get("realized_pnl", 0.0)) + realized_delta
        if realized_delta < 0:
            state["consecutive_loss_count"] = int(state.get("consecutive_loss_count", 0)) + 1
        elif realized_delta > 0:
            state["consecutive_loss_count"] = 0

        prev_slippage = float(state.get("avg_slippage_bps", 0.0))
        state["avg_slippage_bps"] = round((prev_slippage + slippage_bps) / 2 if prev_slippage else slippage_bps, 4)
        state["last_execution_latency_ms"] = execution_latency_ms

        if abs(resulting_qty) < 1e-9:
            positions[symbol] = self._empty_position()
            positions[symbol]["realized_pnl"] = float(current.get("realized_pnl", 0.0)) + realized_delta
        else:
            positions[symbol] = {
                "qty": resulting_qty,
                "side": "long" if resulting_qty > 0 else "short",
                "avg_entry_price": new_avg_entry,
                "mark_price": fill_price,
                "notional": abs(resulting_qty * fill_price),
                "realized_pnl": float(current.get("realized_pnl", 0.0)) + realized_delta,
                "unrealized_pnl": 0.0,
            }

        self.save(state)
        return self.get()

    def build_snapshot(self) -> PaperAccountSnapshot:
        state = self.get()
        positions = [
            PositionSnapshot(
                symbol=symbol,
                qty=float(position.get("qty", 0.0)),
                side=position.get("side", "flat"),
                avg_entry_price=float(position.get("avg_entry_price", 0.0)),
                mark_price=float(position.get("mark_price", 0.0)),
                notional=float(position.get("notional", 0.0)),
                realized_pnl=float(position.get("realized_pnl", 0.0)),
                unrealized_pnl=float(position.get("unrealized_pnl", 0.0)),
            )
            for symbol, position in state.get("positions", {}).items()
            if abs(float(position.get("qty", 0.0))) >= 1e-9
        ]
        updated_at = ensure_utc(datetime.fromisoformat(state.get("updated_at", utc_now().isoformat())))
        return PaperAccountSnapshot(
            snapshot_id=new_snapshot_id("acct"),
            account_mode=state.get("account_mode", self.settings.default_account_mode),
            market_type=state.get("market_type", self.settings.default_market_type),
            equity=float(state.get("equity", self.settings.paper_initial_equity)),
            cash_balance=float(state.get("cash_balance", self.settings.paper_initial_equity)),
            available_balance=float(state.get("available_balance", self.settings.paper_initial_equity)),
            used_margin=float(state.get("used_margin", 0.0)),
            realized_pnl=float(state.get("realized_pnl", 0.0)),
            unrealized_pnl=float(state.get("unrealized_pnl", 0.0)),
            fee_paid_total=float(state.get("fee_paid_total", 0.0)),
            avg_slippage_bps=float(state.get("avg_slippage_bps", 0.0)),
            positions=positions,
            updated_at=updated_at,
        )

    def persist_snapshot(self, session: Session, *, task_id: str | None, symbol: str | None) -> PaperAccountSnapshot:
        snapshot = self.build_snapshot()
        row = PaperAccountSnapshotRow(
            snapshot_id=snapshot.snapshot_id,
            task_id=task_id,
            symbol=symbol,
            market_type=snapshot.market_type,
            account_mode=snapshot.account_mode,
            equity=Decimal(str(snapshot.equity)),
            cash_balance=Decimal(str(snapshot.cash_balance)),
            available_balance=Decimal(str(snapshot.available_balance)),
            used_margin=Decimal(str(snapshot.used_margin)),
            realized_pnl=Decimal(str(snapshot.realized_pnl)),
            unrealized_pnl=Decimal(str(snapshot.unrealized_pnl)),
            avg_slippage_bps=Decimal(str(snapshot.avg_slippage_bps)),
            positions_json=[position.model_dump(mode="json") for position in snapshot.positions],
            raw_payload=snapshot.model_dump(mode="json"),
        )
        session.add(row)
        session.flush()
        return snapshot
