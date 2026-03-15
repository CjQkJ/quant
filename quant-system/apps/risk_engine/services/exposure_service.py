"""仓位暴露服务。"""

from __future__ import annotations

from apps.risk_engine.services.global_risk_service import GlobalRiskService


class ExposureService:
    def __init__(self, global_risk_service: GlobalRiskService) -> None:
        self.global_risk_service = global_risk_service

    def evaluate(self, symbol: str) -> dict:
        state = self.global_risk_service.get_account_state()
        positions = state.get("positions", {})
        position = positions.get(symbol, {})
        equity = float(state["equity"]) or 1.0
        notional = abs(float(position.get("notional", 0.0)))
        return {
            "position": position,
            "total_exposure_ratio": notional / equity if equity else 0.0,
        }

