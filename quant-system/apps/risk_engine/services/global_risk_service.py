"""全局风险服务。"""

from __future__ import annotations

from shared.config.settings import get_settings
from shared.utils.state_store import StateStore


class GlobalRiskService:
    ACCOUNT_KEY = "paper:account"

    def __init__(self, state_store: StateStore) -> None:
        self.state_store = state_store
        self.settings = get_settings()

    def get_account_state(self) -> dict:
        default_state = {
            "equity": self.settings.paper_initial_equity,
            "available_balance": self.settings.paper_initial_equity,
            "used_margin": 0.0,
            "peak_equity": self.settings.paper_initial_equity,
            "consecutive_loss_count": 0,
            "positions": {},
            "avg_slippage_bps": 0.0,
        }
        return self.state_store.get_json(self.ACCOUNT_KEY, default_state)

    def save_account_state(self, state: dict) -> None:
        peak = max(state.get("peak_equity", state["equity"]), state["equity"])
        state["peak_equity"] = peak
        self.state_store.set_json(self.ACCOUNT_KEY, state)

    def evaluate(self) -> dict:
        state = self.get_account_state()
        equity = float(state["equity"])
        available = float(state["available_balance"])
        used_margin = float(state.get("used_margin", 0.0))
        peak = float(state.get("peak_equity", equity or 1.0))
        drawdown_ratio = max(0.0, (peak - equity) / peak) if peak else 0.0
        used_margin_ratio = used_margin / equity if equity else 0.0
        return {
            "equity": equity,
            "available_balance": available,
            "used_margin_ratio": used_margin_ratio,
            "daily_drawdown_ratio": drawdown_ratio,
            "consecutive_loss_count": int(state.get("consecutive_loss_count", 0)),
            "avg_slippage_bps": float(state.get("avg_slippage_bps", 0.0)),
        }

