"""历史回放驱动。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from apps.market_data.schemas.market import OHLCVPayload
from apps.market_data.services.ohlcv_service import OHLCVService


class ReplayRunner:
    def __init__(self, orchestrator) -> None:
        self.orchestrator = orchestrator
        self.ohlcv_service = OHLCVService()

    def run(self, session: Session, bars: list[dict], symbol: str, timeframe: str = "5m") -> list[dict]:
        results: list[dict] = []
        for bar in bars:
            payload = OHLCVPayload.model_validate(bar)
            self.ohlcv_service.save_many(session, [payload])
            session.commit()
            result = self.orchestrator.run_cycle(session, symbol=symbol, timeframe=timeframe)
            session.commit()
            results.append(result.model_dump(mode="json"))
        return results

