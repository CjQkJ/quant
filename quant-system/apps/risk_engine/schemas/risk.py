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
    audit_id: str
    audit_time: datetime
    decision: str
    approved: bool
    risk_level: str
    rejection_reasons: list[str]
    warnings: list[str]
    required_adjustments: list[AuditAdjustment]
    approved_order_plan: dict
    checks: AuditChecks
    audit_summary: str


class AccountStatus(BaseSchema):
    equity: float
    available_balance: float
    used_margin_ratio: float


class RiskMetrics(BaseSchema):
    total_exposure_ratio: float
    daily_drawdown_ratio: float
    consecutive_loss_count: int
    avg_slippage_bps: float


class MonitorAlert(BaseSchema):
    level: str
    code: str
    message: str


class MonitorAction(BaseSchema):
    action: str
    reason: str


class MonitorStatusOutput(BaseSchema):
    monitor_time: datetime
    system_status: str
    account_status: AccountStatus
    risk_metrics: RiskMetrics
    alerts: list[MonitorAlert]
    actions: list[MonitorAction]
    kill_switch: bool

