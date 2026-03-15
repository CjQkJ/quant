"""审核智能体。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from apps.risk_engine.schemas.risk import AuditDecisionOutput
from apps.risk_engine.services.audit_service import AuditService
from apps.strategy_registry.schemas.strategy import StrategySelectionOutput


class AuditorAgent:
    def __init__(self, audit_service: AuditService) -> None:
        self.audit_service = audit_service

    def run(
        self,
        session: Session,
        analysis: AnalysisAgentOutput,
        selection: StrategySelectionOutput,
    ) -> AuditDecisionOutput:
        return self.audit_service.audit(session, analysis=analysis, selection=selection)

