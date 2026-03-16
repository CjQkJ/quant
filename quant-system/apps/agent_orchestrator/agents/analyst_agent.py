"""分析智能体。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput, KeyFactor
from apps.analysis_engine.services.signal_summary_service import SignalSummaryService
from apps.agent_orchestrator.tools.tool_executor import ToolExecutor
from apps.agent_orchestrator.tools.schemas import MarketContextOutput, SymbolTimeframeInput


class AnalystAgent:
    def __init__(self, tool_executor: ToolExecutor | None = None) -> None:
        self.service = SignalSummaryService()
        self.tool_executor = tool_executor or ToolExecutor()

    def run(
        self,
        session: Session,
        task_id: str,
        symbol: str,
        timeframe: str = "5m",
        *,
        force_context_refresh: bool = False,
    ) -> AnalysisAgentOutput:
        analysis = self.service.analyze(session, task_id=task_id, symbol=symbol, timeframe=timeframe)
        needs_more_context = force_context_refresh or analysis.confidence < 0.45 or "stale_market_data" in analysis.risk_flags
        if not needs_more_context:
            return analysis

        _, tool_output = self.tool_executor.execute(
            session,
            role="analyst_agent",
            tool_name="get_market_context",
            payload=SymbolTimeframeInput(symbol=symbol, timeframe=timeframe),
            task_id=task_id,
        )
        market_context = MarketContextOutput.model_validate(tool_output).market_context
        key_factors = list(analysis.key_factors)
        key_factors.append(KeyFactor(name="open_interest", value=f"{market_context.open_interest:.2f}", weight=0.10))
        key_factors.append(KeyFactor(name="funding_refresh", value=f"{market_context.funding_rate:.6f}", weight=0.10))
        risk_flags = sorted(set([*analysis.risk_flags, "supplemental_context_collected"]))
        return analysis.model_copy(
            update={
                "key_factors": key_factors,
                "risk_flags": risk_flags,
                "summary": f"{analysis.summary}, supplemental_context=orderbook_funding_oi_checked",
            }
        )
