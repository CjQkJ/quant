"""paper 账户状态服务。"""

from __future__ import annotations

from shared.config.settings import get_settings
from shared.utils.state_store import StateStore
from shared.utils.time import utc_now


class AccountStateService:
    ACCOUNT_KEY = "paper:account"

    def __init__(self, state_store: StateStore) -> None:
        self.state_store = state_store
        self.settings = get_settings()

    def get(self) -> dict:
        default_state = {
            "mode": "paper",
            "equity": self.settings.paper_initial_equity,
            "available_balance": self.settings.paper_initial_equity,
            "used_margin": 0.0,
            "peak_equity": self.settings.paper_initial_equity,
            "consecutive_loss_count": 0,
            "avg_slippage_bps": 0.0,
            "positions": {},
            "updated_at": utc_now().isoformat(),
        }
        return self.state_store.get_json(self.ACCOUNT_KEY, default_state)

    def save(self, state: dict) -> None:
        state["updated_at"] = utc_now().isoformat()
        self.state_store.set_json(self.ACCOUNT_KEY, state)

    def apply_fill(self, symbol: str, side: str, filled_qty: float, fill_price: float, fee: float, slippage_bps: float) -> dict:
        state = self.get()
        equity = float(state["equity"])
        available = float(state["available_balance"])
        signed_qty = filled_qty if side == "buy" else -filled_qty

        positions = state.setdefault("positions", {})
        current = positions.get(symbol, {"qty": 0.0, "avg_entry_price": 0.0, "notional": 0.0, "side": "flat"})
        new_qty = float(current.get("qty", 0.0)) + signed_qty
        if abs(new_qty) < 1e-9:
            positions[symbol] = {"qty": 0.0, "avg_entry_price": 0.0, "notional": 0.0, "side": "flat"}
        else:
            positions[symbol] = {
                "qty": new_qty,
                "avg_entry_price": fill_price,
                "notional": abs(new_qty * fill_price),
                "side": "long" if new_qty > 0 else "short",
            }

        used_margin = sum(abs(position.get("notional", 0.0)) * 0.1 for position in positions.values())
        state["used_margin"] = used_margin
        state["available_balance"] = max(0.0, available - fee)
        state["equity"] = max(0.0, equity - fee)
        state["peak_equity"] = max(float(state.get("peak_equity", state["equity"])), float(state["equity"]))
        prev_slippage = float(state.get("avg_slippage_bps", 0.0))
        state["avg_slippage_bps"] = round((prev_slippage + slippage_bps) / 2 if prev_slippage else slippage_bps, 4)
        self.save(state)
        return state

