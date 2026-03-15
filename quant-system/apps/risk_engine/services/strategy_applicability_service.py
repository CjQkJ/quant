"""策略适用性检查。"""

from __future__ import annotations

from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from apps.strategy_registry.schemas.strategy import StrategySelectionOutput


class StrategyApplicabilityService:
    def check(self, selection: StrategySelectionOutput, analysis: AnalysisAgentOutput) -> dict:
        enabled = selection.selected_strategy_id != ""
        fit_score_ok = selection.fit_score >= 0.35
        confidence_ok = analysis.confidence >= 0.25
        return {
            "enabled": enabled,
            "fit_score_ok": fit_score_ok,
            "confidence_ok": confidence_ok,
        }

