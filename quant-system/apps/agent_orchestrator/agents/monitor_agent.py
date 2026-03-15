"""监控智能体。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from apps.risk_engine.schemas.risk import MonitorStatusOutput
from apps.risk_engine.services.monitor_service import MonitorService


class MonitorAgent:
    def __init__(self, monitor_service: MonitorService) -> None:
        self.monitor_service = monitor_service

    def run(self, session: Session, symbol: str) -> MonitorStatusOutput:
        return self.monitor_service.run_cycle(session, symbol=symbol)

