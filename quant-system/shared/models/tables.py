"""第一阶段核心表。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.db.base import Base, JsonDocument
from shared.models.common import CreatedAtMixin, CreatedUpdatedMixin

PrimaryKeyInt = BigInteger().with_variant(Integer, "sqlite")


class MarketOHLCV(Base, CreatedAtMixin):
    __tablename__ = "market_ohlcv"
    __table_args__ = (UniqueConstraint("exchange", "symbol", "timeframe", "open_time"),)

    id: Mapped[int] = mapped_column(PrimaryKeyInt, primary_key=True, autoincrement=True)
    exchange: Mapped[str] = mapped_column(String(32), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    timeframe: Mapped[str] = mapped_column(String(16), index=True)
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    close_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    open: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    high: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    low: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    close: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    volume: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    quote_volume: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    trade_count: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(64))


class MarketOrderBookSnapshot(Base, CreatedAtMixin):
    __tablename__ = "market_orderbook_snapshot"

    id: Mapped[int] = mapped_column(PrimaryKeyInt, primary_key=True, autoincrement=True)
    exchange: Mapped[str] = mapped_column(String(32), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    snapshot_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    best_bid: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    best_ask: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    bid_depth_json: Mapped[list[dict[str, Any]]] = mapped_column(JsonDocument)
    ask_depth_json: Mapped[list[dict[str, Any]]] = mapped_column(JsonDocument)
    spread: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    source: Mapped[str] = mapped_column(String(64))


class MarketTradeTick(Base, CreatedAtMixin):
    __tablename__ = "market_trade_tick"
    __table_args__ = (UniqueConstraint("exchange", "symbol", "trade_id"),)

    id: Mapped[int] = mapped_column(PrimaryKeyInt, primary_key=True, autoincrement=True)
    exchange: Mapped[str] = mapped_column(String(32), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    trade_id: Mapped[str] = mapped_column(String(64))
    trade_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    qty: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    side: Mapped[str] = mapped_column(String(8))
    is_buyer_maker: Mapped[bool | None] = mapped_column(Boolean)
    source: Mapped[str] = mapped_column(String(64))


class MarketDerivativesMetric(Base, CreatedAtMixin):
    __tablename__ = "market_derivatives_metric"
    __table_args__ = (UniqueConstraint("exchange", "symbol", "metric_time", "metric_type"),)

    id: Mapped[int] = mapped_column(PrimaryKeyInt, primary_key=True, autoincrement=True)
    exchange: Mapped[str] = mapped_column(String(32), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    metric_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    metric_type: Mapped[str] = mapped_column(String(32), index=True)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    extra_json: Mapped[dict[str, Any] | None] = mapped_column(JsonDocument)
    source: Mapped[str] = mapped_column(String(64))


class StrategyMetadata(Base, CreatedUpdatedMixin):
    __tablename__ = "strategy_metadata"

    id: Mapped[int] = mapped_column(PrimaryKeyInt, primary_key=True, autoincrement=True)
    strategy_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    strategy_name: Mapped[str] = mapped_column(String(128))
    strategy_type: Mapped[str] = mapped_column(String(64), index=True)
    description: Mapped[str] = mapped_column(Text)
    supported_exchange: Mapped[str] = mapped_column(String(32))
    supported_symbol: Mapped[str] = mapped_column(String(32))
    supported_timeframe: Mapped[str] = mapped_column(String(16))
    market_regime_fit: Mapped[list[str]] = mapped_column(JsonDocument)
    directional_fit: Mapped[list[str]] = mapped_column(JsonDocument)
    risk_level: Mapped[str] = mapped_column(String(16))
    max_position_ratio: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    leverage_allowed: Mapped[bool] = mapped_column(Boolean)
    cooldown_seconds: Mapped[int] = mapped_column(Integer)
    disable_conditions: Mapped[list[str] | None] = mapped_column(JsonDocument)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[str] = mapped_column(String(32))


class AnalysisReport(Base, CreatedAtMixin):
    __tablename__ = "analysis_report"

    id: Mapped[int] = mapped_column(PrimaryKeyInt, primary_key=True, autoincrement=True)
    analysis_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    task_id: Mapped[str] = mapped_column(String(64), index=True)
    analysis_version: Mapped[str] = mapped_column(String(32), default="analysis.v3")
    exchange: Mapped[str] = mapped_column(String(32))
    symbol: Mapped[str] = mapped_column(String(32))
    timeframe: Mapped[str] = mapped_column(String(16))
    regime: Mapped[str] = mapped_column(String(32))
    bias: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    volatility_level: Mapped[str] = mapped_column(String(16))
    liquidity_level: Mapped[str] = mapped_column(String(16))
    key_factors: Mapped[list[dict[str, Any]]] = mapped_column(JsonDocument)
    risk_flags: Mapped[list[str]] = mapped_column(JsonDocument)
    suggested_strategy_types: Mapped[list[str]] = mapped_column(JsonDocument)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JsonDocument)
    created_by_agent: Mapped[str] = mapped_column(String(64))


class StrategySelection(Base, CreatedAtMixin):
    __tablename__ = "strategy_selection"

    id: Mapped[int] = mapped_column(PrimaryKeyInt, primary_key=True, autoincrement=True)
    selection_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    task_id: Mapped[str] = mapped_column(String(64), index=True)
    analysis_id: Mapped[str] = mapped_column(String(64), index=True)
    ranking_version: Mapped[str] = mapped_column(String(32), default="ranking.v3")
    selected_strategy_id: Mapped[str] = mapped_column(String(64))
    selected_strategy_name: Mapped[str] = mapped_column(String(128))
    selected_strategy_type: Mapped[str] = mapped_column(String(64))
    candidate_strategies: Mapped[list[dict[str, Any]]] = mapped_column(JsonDocument)
    selection_reason: Mapped[str] = mapped_column(Text)
    fit_score: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    fallback_strategy_id: Mapped[str | None] = mapped_column(String(64))
    switch_attempted: Mapped[bool] = mapped_column(Boolean, default=False)
    cooldown_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    selection_policy_note: Mapped[str] = mapped_column(String(64), default="normal")
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JsonDocument)
    created_by_agent: Mapped[str] = mapped_column(String(64))


class AuditDecision(Base, CreatedAtMixin):
    __tablename__ = "audit_decision"

    id: Mapped[int] = mapped_column(PrimaryKeyInt, primary_key=True, autoincrement=True)
    audit_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    task_id: Mapped[str] = mapped_column(String(64), index=True)
    analysis_id: Mapped[str] = mapped_column(String(64), index=True)
    selection_id: Mapped[str] = mapped_column(String(64), index=True)
    strategy_signal_id: Mapped[str | None] = mapped_column(String(64), index=True)
    risk_policy_version: Mapped[str] = mapped_column(String(32), default="risk-policy.v3")
    approved: Mapped[bool] = mapped_column(Boolean)
    decision: Mapped[str] = mapped_column(String(32))
    risk_level: Mapped[str] = mapped_column(String(16))
    rejection_reasons: Mapped[list[str]] = mapped_column(JsonDocument)
    warnings: Mapped[list[str]] = mapped_column(JsonDocument)
    required_adjustments: Mapped[list[dict[str, Any]]] = mapped_column(JsonDocument)
    approved_order_plan: Mapped[dict[str, Any]] = mapped_column(JsonDocument)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JsonDocument)
    created_by_agent: Mapped[str] = mapped_column(String(64))


class ExecutionOrder(Base, CreatedUpdatedMixin):
    __tablename__ = "execution_order"

    id: Mapped[int] = mapped_column(PrimaryKeyInt, primary_key=True, autoincrement=True)
    exec_order_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    task_id: Mapped[str] = mapped_column(String(64), index=True)
    audit_id: Mapped[str] = mapped_column(String(64), index=True)
    strategy_signal_id: Mapped[str | None] = mapped_column(String(64), index=True)
    exchange: Mapped[str] = mapped_column(String(32))
    symbol: Mapped[str] = mapped_column(String(32))
    market_type: Mapped[str] = mapped_column(String(16), default="futures")
    account_mode: Mapped[str] = mapped_column(String(16), default="paper")
    side: Mapped[str] = mapped_column(String(16))
    position_side: Mapped[str] = mapped_column(String(16))
    order_type: Mapped[str] = mapped_column(String(16))
    execution_mode: Mapped[str] = mapped_column(String(16), default="paper")
    price: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    status: Mapped[str] = mapped_column(String(32))
    exchange_order_id: Mapped[str | None] = mapped_column(String(128))
    client_order_id: Mapped[str | None] = mapped_column(String(128))
    avg_fill_price: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    filled_qty: Mapped[Decimal] = mapped_column(Numeric(24, 8), default=0)
    fee: Mapped[Decimal] = mapped_column(Numeric(24, 8), default=0)
    estimated_slippage_bps: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(24, 8), default=0)
    unrealized_pnl_at_fill: Mapped[Decimal] = mapped_column(Numeric(24, 8), default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    placed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    filled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TaskEventLog(Base, CreatedAtMixin):
    __tablename__ = "task_event_log"

    id: Mapped[int] = mapped_column(PrimaryKeyInt, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    event_source: Mapped[str] = mapped_column(String(64))
    event_payload: Mapped[dict[str, Any]] = mapped_column(JsonDocument)
    message: Mapped[str] = mapped_column(Text)
    level: Mapped[str] = mapped_column(String(16), default="info")


class StrategySignalRecord(Base, CreatedAtMixin):
    __tablename__ = "strategy_signal"
    __table_args__ = (UniqueConstraint("signal_id"),)

    id: Mapped[int] = mapped_column(PrimaryKeyInt, primary_key=True, autoincrement=True)
    signal_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    task_id: Mapped[str] = mapped_column(String(64), index=True)
    analysis_id: Mapped[str] = mapped_column(String(64), index=True)
    selection_id: Mapped[str] = mapped_column(String(64), index=True)
    strategy_id: Mapped[str] = mapped_column(String(64), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    timeframe: Mapped[str] = mapped_column(String(16))
    market_type: Mapped[str] = mapped_column(String(16), default="futures")
    action: Mapped[str] = mapped_column(String(16))
    direction: Mapped[str] = mapped_column(String(16))
    strength: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    target_position_ratio: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    reason: Mapped[str] = mapped_column(Text)
    risk_tags: Mapped[list[str]] = mapped_column(JsonDocument)
    strategy_runtime_version: Mapped[str] = mapped_column(String(32))
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JsonDocument)


class PaperAccountSnapshot(Base, CreatedAtMixin):
    __tablename__ = "paper_account_snapshot"

    id: Mapped[int] = mapped_column(PrimaryKeyInt, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    task_id: Mapped[str | None] = mapped_column(String(64), index=True)
    symbol: Mapped[str | None] = mapped_column(String(32), index=True)
    market_type: Mapped[str] = mapped_column(String(16), default="futures")
    account_mode: Mapped[str] = mapped_column(String(16), default="paper")
    equity: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    available_balance: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    used_margin: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(24, 8), default=0)
    unrealized_pnl: Mapped[Decimal] = mapped_column(Numeric(24, 8), default=0)
    avg_slippage_bps: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)
    positions_json: Mapped[list[dict[str, Any]]] = mapped_column(JsonDocument)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JsonDocument)


class MonitorSnapshot(Base, CreatedAtMixin):
    __tablename__ = "monitor_snapshot"

    id: Mapped[int] = mapped_column(PrimaryKeyInt, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    task_id: Mapped[str | None] = mapped_column(String(64), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    risk_policy_version: Mapped[str] = mapped_column(String(32))
    system_status: Mapped[str] = mapped_column(String(16))
    account_status_json: Mapped[dict[str, Any]] = mapped_column(JsonDocument)
    risk_metrics_json: Mapped[dict[str, Any]] = mapped_column(JsonDocument)
    source_freshness_json: Mapped[list[dict[str, Any]]] = mapped_column(JsonDocument)
    alerts_json: Mapped[list[dict[str, Any]]] = mapped_column(JsonDocument)
    actions_json: Mapped[list[dict[str, Any]]] = mapped_column(JsonDocument)
    suggestions_json: Mapped[list[dict[str, Any]]] = mapped_column(JsonDocument)
    kill_switch: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JsonDocument)


class ReplayRun(Base, CreatedAtMixin):
    __tablename__ = "replay_run"

    id: Mapped[int] = mapped_column(PrimaryKeyInt, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    timeframe: Mapped[str] = mapped_column(String(16))
    fixture_name: Mapped[str] = mapped_column(String(128))
    analysis_version: Mapped[str] = mapped_column(String(32))
    ranking_version: Mapped[str] = mapped_column(String(32))
    risk_policy_version: Mapped[str] = mapped_column(String(32))
    strategy_runtime_version: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary_json: Mapped[dict[str, Any] | None] = mapped_column(JsonDocument)


class ReplayCycleResult(Base, CreatedAtMixin):
    __tablename__ = "replay_cycle_result"

    id: Mapped[int] = mapped_column(PrimaryKeyInt, primary_key=True, autoincrement=True)
    cycle_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    task_id: Mapped[str] = mapped_column(String(64), index=True)
    cycle_index: Mapped[int] = mapped_column(Integer, index=True)
    bar_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    selected_strategy_id: Mapped[str] = mapped_column(String(64))
    strategy_signal_action: Mapped[str] = mapped_column(String(16))
    strategy_signal_direction: Mapped[str] = mapped_column(String(16))
    audit_decision: Mapped[str] = mapped_column(String(32))
    execution_status: Mapped[str] = mapped_column(String(32))
    switch_attempted: Mapped[bool] = mapped_column(Boolean, default=False)
    cooldown_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    account_snapshot_json: Mapped[dict[str, Any]] = mapped_column(JsonDocument)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JsonDocument)
