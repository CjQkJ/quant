"""风控输出结构。"""

from __future__ import annotations

from datetime import datetime

from shared.schemas.base import BaseSchema


class AuditAdjustment(BaseSchema):
    field: str
    original: float
    adjusted: float
    reason: str


class AuditChecks(BaseSchema):
    global_risk_limit_ok: bool
    strategy_applicability_ok: bool
    exposure_ok: bool
    liquidity_ok: bool
    event_risk_ok: bool


class AuditDecisionOutput(BaseSchema):
    task_id: str
    analysis_id: str
    selection_id: str
    strategy_signal_id: str | None = None
    audit_id: str
    audit_time: datetime
    risk_policy_version: str
    decision: str
    approved: bool
    risk_level: str
    next_action: str = "none"
    context_requirements: list[str]
    rejection_reasons: list[str]
    warnings: list[str]
    required_adjustments: list[AuditAdjustment]
    approved_order_plan: dict
    checks: AuditChecks
    audit_summary: str


class AccountStatus(BaseSchema):
    equity: float
    cash_balance: float
    available_balance: float
    used_margin_ratio: float
    realized_pnl: float
    unrealized_pnl: float


class RiskMetrics(BaseSchema):
    total_exposure_ratio: float
    daily_drawdown_ratio: float
    consecutive_loss_count: int
    avg_slippage_bps: float
    execution_latency_ms: float
    margin_usage_ratio: float


class MonitorAlert(BaseSchema):
    level: str
    code: str
    message: str


class MonitorAction(BaseSchema):
    action: str
    reason: str


class SourceFreshnessStatus(BaseSchema):
    source: str
    age_seconds: float | None = None
    expected_max_age_seconds: float
    is_stale: bool
    missing: bool = False


class MonitorStatusOutput(BaseSchema):
    snapshot_id: str
    monitor_time: datetime
    symbol: str
    risk_policy_version: str
    system_status: str
    account_status: AccountStatus
    risk_metrics: RiskMetrics
    alerts: list[MonitorAlert]
    actions: list[MonitorAction]
    suggestions: list[MonitorAction]
    source_freshness: list[SourceFreshnessStatus]
    kill_switch: bool
