"""监控服务。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.risk_engine.schemas.risk import (
    AccountStatus,
    MonitorAction,
    MonitorAlert,
    MonitorStatusOutput,
    RiskMetrics,
    SourceFreshnessStatus,
)
from apps.risk_engine.services.exposure_service import ExposureService
from apps.risk_engine.services.global_risk_service import GlobalRiskService
from apps.risk_engine.services.kill_switch_service import KillSwitchService
from shared.config.risk_policy import get_risk_policy
from shared.models.enums import SystemStatus
from shared.models.tables import (
    AnalysisReport,
    ExecutionOrder,
    MarketDerivativesMetric,
    MarketOHLCV,
    MarketOrderBookSnapshot,
    MonitorSnapshot,
    StrategySignalRecord,
)
from shared.utils.ids import new_snapshot_id
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

    def _build_freshness_status(
        self,
        source: str,
        observed_at: datetime | None,
        expected_max_age_seconds: float,
    ) -> SourceFreshnessStatus:
        if observed_at is None:
            return SourceFreshnessStatus(
                source=source,
                age_seconds=None,
                expected_max_age_seconds=expected_max_age_seconds,
                is_stale=True,
                missing=True,
            )

        age_seconds = max((utc_now() - ensure_utc(observed_at)).total_seconds(), 0.0)
        return SourceFreshnessStatus(
            source=source,
            age_seconds=age_seconds,
            expected_max_age_seconds=expected_max_age_seconds,
            is_stale=age_seconds > expected_max_age_seconds,
            missing=False,
        )

    def _collect_source_freshness(self, session: Session, symbol: str) -> list[SourceFreshnessStatus]:
        latest_bar_close = session.scalar(
            select(MarketOHLCV.close_time)
            .where(MarketOHLCV.symbol == symbol)
            .order_by(MarketOHLCV.close_time.desc())
            .limit(1)
        )
        latest_orderbook_time = session.scalar(
            select(MarketOrderBookSnapshot.snapshot_time)
            .where(MarketOrderBookSnapshot.symbol == symbol)
            .order_by(MarketOrderBookSnapshot.snapshot_time.desc())
            .limit(1)
        )
        latest_derivatives_time = session.scalar(
            select(MarketDerivativesMetric.metric_time)
            .where(MarketDerivativesMetric.symbol == symbol)
            .order_by(MarketDerivativesMetric.metric_time.desc())
            .limit(1)
        )
        latest_analysis_time = session.scalar(
            select(AnalysisReport.created_at).where(AnalysisReport.symbol == symbol).order_by(AnalysisReport.created_at.desc()).limit(1)
        )
        latest_strategy_signal_time = session.scalar(
            select(StrategySignalRecord.created_at)
            .where(StrategySignalRecord.symbol == symbol)
            .order_by(StrategySignalRecord.created_at.desc())
            .limit(1)
        )

        return [
            self._build_freshness_status("ohlcv", latest_bar_close, 600),
            self._build_freshness_status("orderbook", latest_orderbook_time, 120),
            self._build_freshness_status("derivatives_metrics", latest_derivatives_time, 900),
            self._build_freshness_status("analysis_output", latest_analysis_time, 900),
            self._build_freshness_status("strategy_signal", latest_strategy_signal_time, 900),
        ]

    def run_cycle(self, session: Session, symbol: str) -> MonitorStatusOutput:
        policy = get_risk_policy()
        alerts: list[MonitorAlert] = []
        actions: list[MonitorAction] = []
        suggestions: list[MonitorAction] = []
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

        source_freshness = self._collect_source_freshness(session, symbol)
        stale_sources = [item.source for item in source_freshness if item.is_stale and item.source != "ohlcv"]
        if stale_sources:
            if system_status == SystemStatus.OK:
                system_status = SystemStatus.WARNING
            alerts.append(
                MonitorAlert(
                    level="warn",
                    code="SOURCE_FRESHNESS_WARN",
                    message=f"以下数据源过期或缺失: {', '.join(stale_sources)}",
                )
            )
            suggestions.append(MonitorAction(action="suggest_replay", reason="存在过期或缺失数据源，建议先做 replay 对照"))
            if "strategy_signal" in stale_sources or "analysis_output" in stale_sources:
                suggestions.append(MonitorAction(action="suggest_strategy_pause", reason="分析或信号已过期，建议暂停对应策略"))

        failures = session.scalar(select(func.count()).select_from(ExecutionOrder).where(ExecutionOrder.status == "failed")) or 0
        global_risk = self.global_risk_service.evaluate()
        exposure = self.exposure_service.evaluate(symbol)

        if failures >= 3:
            system_status = SystemStatus.WARNING if system_status == SystemStatus.OK else system_status
            alerts.append(MonitorAlert(level="warn", code="ORDER_FAILURE_RATE", message="近期订单失败次数偏高"))
            suggestions.append(MonitorAction(action="suggest_replay", reason="执行失败率偏高，建议回放最近场景"))
        if exposure["total_exposure_ratio"] >= policy.exposure_limit or global_risk["daily_drawdown_ratio"] >= policy.drawdown_limit:
            system_status = SystemStatus.HALTED
            self.kill_switch_service.set_enabled(True)
            alerts.append(MonitorAlert(level="critical", code="KILL_SWITCH_TRIGGERED", message="风控阈值已触发"))
            actions.append(MonitorAction(action="halt_system", reason="超过风险阈值"))
            suggestions.append(MonitorAction(action="suggest_policy_compare", reason="风控已触发，建议比较不同风险参数版本"))
        elif exposure["total_exposure_ratio"] >= policy.exposure_limit * 0.7 or global_risk["daily_drawdown_ratio"] >= policy.drawdown_limit * 0.7:
            suggestions.append(MonitorAction(action="suggest_policy_compare", reason="风险接近阈值，建议比较风险策略版本"))

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
            suggestions=suggestions,
            source_freshness=source_freshness,
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
                source_freshness_json=[item.model_dump(mode="json") for item in output.source_freshness],
                alerts_json=[alert.model_dump(mode="json") for alert in output.alerts],
                actions_json=[action.model_dump(mode="json") for action in output.actions],
                suggestions_json=[item.model_dump(mode="json") for item in output.suggestions],
                kill_switch=output.kill_switch,
                raw_payload=output.model_dump(mode="json"),
            )
        )
        session.flush()
        return output
