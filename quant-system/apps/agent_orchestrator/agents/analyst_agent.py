"""分析智能体。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from apps.analysis_engine.services.signal_summary_service import SignalSummaryService


class AnalystAgent:
    def __init__(self) -> None:
        self.service = SignalSummaryService()

    def run(self, session: Session, task_id: str, symbol: str, timeframe: str = "5m") -> AnalysisAgentOutput:
        return self.service.analyze(session, task_id=task_id, symbol=symbol, timeframe=timeframe)

