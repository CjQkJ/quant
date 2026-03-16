"""审核服务。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from apps.analysis_engine.schemas.analysis import AnalysisAgentOutput
from apps.risk_engine.schemas.risk import AuditAdjustment, AuditChecks, AuditDecisionOutput
from apps.risk_engine.services.exposure_service import ExposureService
from apps.risk_engine.services.global_risk_service import GlobalRiskService
from apps.risk_engine.services.kill_switch_service import KillSwitchService
from apps.risk_engine.services.strategy_applicability_service import StrategyApplicabilityService
from apps.strategy_registry.schemas.strategy import StrategySelectionOutput
from apps.strategy_runtime.schemas.signal import StrategySignal
from shared.config.risk_policy import get_risk_policy
from shared.models.enums import AuditDecisionType, RiskLevel
from shared.models.tables import AuditDecision
from shared.utils.ids import new_audit_id
from shared.utils.time import utc_now


class AuditService:
    def __init__(
        self,
        kill_switch_service: KillSwitchService,
        global_risk_service: GlobalRiskService,
        exposure_service: ExposureService,
        applicability_service: StrategyApplicabilityService,
    ) -> None:
        self.kill_switch_service = kill_switch_service
        self.global_risk_service = global_risk_service
        self.exposure_service = exposure_service
        self.applicability_service = applicability_service

    def audit(
        self,
        session: Session,
        analysis: AnalysisAgentOutput,
        selection: StrategySelectionOutput,
        strategy_signal: StrategySignal,
    ) -> AuditDecisionOutput:
        policy = get_risk_policy()
        warnings: list[str] = []
        rejection_reasons: list[str] = []
        adjustments: list[AuditAdjustment] = []
        decision = AuditDecisionType.APPROVE
        approved = True
        risk_level = RiskLevel.MEDIUM

        if self.kill_switch_service.is_enabled():
            rejection_reasons.append("kill_switch_enabled")

        global_risk = self.global_risk_service.evaluate()
        exposure = self.exposure_service.evaluate(analysis.symbol)
        applicability = self.applicability_service.check(selection, analysis)

        if global_risk["daily_drawdown_ratio"] >= policy.drawdown_limit:
            rejection_reasons.append("drawdown_limit_exceeded")
        if exposure["total_exposure_ratio"] >= policy.exposure_limit:
            rejection_reasons.append("exposure_limit_exceeded")
        if not all(applicability.values()):
            rejection_reasons.append("strategy_not_applicable")
        if analysis.liquidity_level in policy.low_liquidity_levels and strategy_signal.action == "entry":
            rejection_reasons.append("liquidity_too_low_for_entry")
        if any(flag in policy.event_risk_blocklist for flag in analysis.risk_flags):
            rejection_reasons.append("event_risk_blocked")

        if rejection_reasons:
            decision = AuditDecisionType.REJECT
            approved = False
            risk_level = RiskLevel.HIGH
        elif strategy_signal.action in {"no_trade", "hold"} or selection.selected_strategy_id.startswith("defensive") or analysis.confidence < policy.observe_confidence_lt:
            decision = AuditDecisionType.OBSERVE_ONLY
            approved = False
            risk_level = RiskLevel.LOW
            warnings.append("low_confidence_or_signal_no_trade")
        elif analysis.confidence < policy.downgrade_confidence_lt or analysis.volatility_level in policy.high_volatility_levels or strategy_signal.action == "reduce":
            decision = AuditDecisionType.DOWNGRADE
            approved = True
            risk_level = RiskLevel.MEDIUM
            adjustments.append(
                AuditAdjustment(
                    field="position_size_ratio",
                    original=policy.default_max_position_ratio,
                    adjusted=policy.downgraded_max_position_ratio,
                    reason="在中等风险或高波动环境下缩小仓位",
                )
            )
            warnings.append("reduced_position_size")
        else:
            warnings.append("standard_risk_profile")

        approved_order_plan = {
            "entry_mode": "limit" if decision == AuditDecisionType.DOWNGRADE else "market",
            "max_position_ratio": adjustments[0].adjusted if adjustments else policy.default_max_position_ratio,
            "leverage": 1,
            "time_in_force": "GTC",
            "allow_execution": approved,
        }
        checks = AuditChecks(
            global_risk_limit_ok=global_risk["daily_drawdown_ratio"] < policy.drawdown_limit and not self.kill_switch_service.is_enabled(),
            strategy_applicability_ok=all(applicability.values()),
            exposure_ok=exposure["total_exposure_ratio"] < policy.exposure_limit,
            liquidity_ok=analysis.liquidity_level not in policy.low_liquidity_levels,
            event_risk_ok=not any(flag in policy.event_risk_blocklist for flag in analysis.risk_flags),
        )

        output = AuditDecisionOutput(
            task_id=analysis.task_id,
            analysis_id=analysis.analysis_id,
            selection_id=selection.selection_id,
            strategy_signal_id=strategy_signal.signal_id,
            audit_id=new_audit_id(),
            audit_time=utc_now(),
            risk_policy_version=policy.version,
            decision=decision,
            approved=approved,
            risk_level=risk_level,
            rejection_reasons=rejection_reasons,
            warnings=warnings,
            required_adjustments=adjustments,
            approved_order_plan=approved_order_plan,
            checks=checks,
            audit_summary=f"decision={decision}, risk_level={risk_level}",
        )

        row = AuditDecision(
            audit_id=output.audit_id,
            task_id=output.task_id,
            analysis_id=output.analysis_id,
            selection_id=output.selection_id,
            strategy_signal_id=output.strategy_signal_id,
            risk_policy_version=output.risk_policy_version,
            approved=output.approved,
            decision=output.decision,
            risk_level=output.risk_level,
            rejection_reasons=output.rejection_reasons,
            warnings=output.warnings,
            required_adjustments=[item.model_dump() for item in output.required_adjustments],
            approved_order_plan=output.approved_order_plan,
            raw_payload=output.model_dump(mode="json"),
            created_by_agent="auditor_agent",
        )
        session.add(row)
        session.flush()
        return output
