"""监控服务。"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from shared.config.risk_policy import get_risk_policy
from shared.models.tables import ExecutionOrder, MarketOHLCV, MonitorSnapshot
from shared.utils.ids import new_snapshot_id
from apps.risk_engine.schemas.risk import (
    AccountStatus,
    MonitorAction,
    MonitorAlert,
    MonitorStatusOutput,
    RiskMetrics,
)
from apps.risk_engine.services.exposure_service import ExposureService
from apps.risk_engine.services.global_risk_service import GlobalRiskService
from apps.risk_engine.services.kill_switch_service import KillSwitchService
from shared.models.enums import SystemStatus
from shared.utils.time import ensure_utc, utc_now


class MonitorService:
    def __init__(
        self,
        kill_switch_service: KillSwitchService,
        global_risk_service: GlobalRiskService,
        exposure_service: ExposureService,
    ) -> None:
        self.kill_switch_service = kill_switch_service
        self.global_risk_service = global_risk_service
        self.exposure_service = exposure_service

    def run_cycle(self, session: Session, symbol: str) -> MonitorStatusOutput:
        policy = get_risk_policy()
        alerts: list[MonitorAlert] = []
        actions: list[MonitorAction] = []
        system_status = SystemStatus.OK

        latest_bar = session.scalar(
            select(MarketOHLCV).where(MarketOHLCV.symbol == symbol).order_by(MarketOHLCV.close_time.desc()).limit(1)
        )
        if latest_bar is not None:
            staleness = (utc_now() - ensure_utc(latest_bar.close_time)).total_seconds()
            if staleness > 1800:
                system_status = SystemStatus.CRITICAL
                alerts.append(MonitorAlert(level="critical", code="STALE_MARKET_DATA", message="市场数据已过期"))
            elif staleness > 600:
                system_status = SystemStatus.WARNING
                alerts.append(MonitorAlert(level="warn", code="MARKET_DATA_DELAY", message="市场数据延迟超过 10 分钟"))

        failures = session.scalar(select(func.count()).select_from(ExecutionOrder).where(ExecutionOrder.status == "failed")) or 0
        global_risk = self.global_risk_service.evaluate()
        exposure = self.exposure_service.evaluate(symbol)

        if failures >= 3:
            system_status = SystemStatus.WARNING if system_status == SystemStatus.OK else system_status
            alerts.append(MonitorAlert(level="warn", code="ORDER_FAILURE_RATE", message="近期订单失败次数偏高"))
        if exposure["total_exposure_ratio"] >= policy.exposure_limit or global_risk["daily_drawdown_ratio"] >= policy.drawdown_limit:
            system_status = SystemStatus.HALTED
            self.kill_switch_service.set_enabled(True)
            alerts.append(MonitorAlert(level="critical", code="KILL_SWITCH_TRIGGERED", message="风控阈值已触发"))
            actions.append(MonitorAction(action="halt_system", reason="超过风险阈值"))

        kill_switch = self.kill_switch_service.is_enabled()
        if kill_switch and not actions:
            system_status = SystemStatus.HALTED
            actions.append(MonitorAction(action="halt_system", reason="kill switch 已开启"))
        elif not actions:
            actions.append(MonitorAction(action="keep_running", reason="系统风险处于可接受范围"))

        output = MonitorStatusOutput(
            snapshot_id=new_snapshot_id("monitor"),
            monitor_time=utc_now(),
            symbol=symbol,
            risk_policy_version=policy.version,
            system_status=system_status,
            account_status=AccountStatus(
                equity=global_risk["equity"],
                cash_balance=global_risk["cash_balance"],
                available_balance=global_risk["available_balance"],
                used_margin_ratio=global_risk["used_margin_ratio"],
                realized_pnl=global_risk["realized_pnl"],
                unrealized_pnl=global_risk["unrealized_pnl"],
            ),
            risk_metrics=RiskMetrics(
                total_exposure_ratio=exposure["total_exposure_ratio"],
                daily_drawdown_ratio=global_risk["daily_drawdown_ratio"],
                consecutive_loss_count=global_risk["consecutive_loss_count"],
                avg_slippage_bps=global_risk["avg_slippage_bps"],
                execution_latency_ms=global_risk["execution_latency_ms"],
                margin_usage_ratio=global_risk["margin_usage_ratio"],
            ),
            alerts=alerts,
            actions=actions,
            kill_switch=kill_switch,
        )
        session.add(
            MonitorSnapshot(
                snapshot_id=output.snapshot_id,
                task_id=None,
                symbol=symbol,
                risk_policy_version=output.risk_policy_version,
                system_status=output.system_status,
                account_status_json=output.account_status.model_dump(mode="json"),
                risk_metrics_json=output.risk_metrics.model_dump(mode="json"),
                alerts_json=[alert.model_dump(mode="json") for alert in output.alerts],
                actions_json=[action.model_dump(mode="json") for action in output.actions],
                kill_switch=output.kill_switch,
                raw_payload=output.model_dump(mode="json"),
            )
        )
        session.flush()
        return output
