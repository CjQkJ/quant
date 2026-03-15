"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-03-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pk_type = sa.BigInteger().with_variant(sa.Integer(), "sqlite")
    json_type = sa.JSON()
    op.create_table(
        "market_ohlcv",
        sa.Column("id", pk_type, primary_key=True, autoincrement=True),
        sa.Column("exchange", sa.String(32), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("timeframe", sa.String(16), nullable=False),
        sa.Column("open_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("close_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(24, 8), nullable=False),
        sa.Column("high", sa.Numeric(24, 8), nullable=False),
        sa.Column("low", sa.Numeric(24, 8), nullable=False),
        sa.Column("close", sa.Numeric(24, 8), nullable=False),
        sa.Column("volume", sa.Numeric(24, 8), nullable=False),
        sa.Column("quote_volume", sa.Numeric(24, 8), nullable=False),
        sa.Column("trade_count", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.UniqueConstraint("exchange", "symbol", "timeframe", "open_time"),
    )
    op.create_table(
        "market_orderbook_snapshot",
        sa.Column("id", pk_type, primary_key=True, autoincrement=True),
        sa.Column("exchange", sa.String(32), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("snapshot_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("best_bid", sa.Numeric(24, 8), nullable=False),
        sa.Column("best_ask", sa.Numeric(24, 8), nullable=False),
        sa.Column("bid_depth_json", json_type, nullable=False),
        sa.Column("ask_depth_json", json_type, nullable=False),
        sa.Column("spread", sa.Numeric(24, 8), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
    )
    op.create_table(
        "market_trade_tick",
        sa.Column("id", pk_type, primary_key=True, autoincrement=True),
        sa.Column("exchange", sa.String(32), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("trade_id", sa.String(64), nullable=False),
        sa.Column("trade_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price", sa.Numeric(24, 8), nullable=False),
        sa.Column("qty", sa.Numeric(24, 8), nullable=False),
        sa.Column("side", sa.String(8), nullable=False),
        sa.Column("is_buyer_maker", sa.Boolean(), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.UniqueConstraint("exchange", "symbol", "trade_id"),
    )
    op.create_table(
        "market_derivatives_metric",
        sa.Column("id", pk_type, primary_key=True, autoincrement=True),
        sa.Column("exchange", sa.String(32), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("metric_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metric_type", sa.String(32), nullable=False),
        sa.Column("metric_value", sa.Numeric(24, 10), nullable=False),
        sa.Column("extra_json", json_type, nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.UniqueConstraint("exchange", "symbol", "metric_time", "metric_type"),
    )
    op.create_table(
        "strategy_metadata",
        sa.Column("id", pk_type, primary_key=True, autoincrement=True),
        sa.Column("strategy_id", sa.String(64), nullable=False, unique=True),
        sa.Column("strategy_name", sa.String(128), nullable=False),
        sa.Column("strategy_type", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("supported_exchange", sa.String(32), nullable=False),
        sa.Column("supported_symbol", sa.String(32), nullable=False),
        sa.Column("supported_timeframe", sa.String(16), nullable=False),
        sa.Column("market_regime_fit", json_type, nullable=False),
        sa.Column("directional_fit", json_type, nullable=False),
        sa.Column("risk_level", sa.String(16), nullable=False),
        sa.Column("max_position_ratio", sa.Numeric(10, 4), nullable=False),
        sa.Column("leverage_allowed", sa.Boolean(), nullable=False),
        sa.Column("cooldown_seconds", sa.Integer(), nullable=False),
        sa.Column("disable_conditions", json_type, nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
    )
    op.create_table(
        "analysis_report",
        sa.Column("id", pk_type, primary_key=True, autoincrement=True),
        sa.Column("analysis_id", sa.String(64), nullable=False, unique=True),
        sa.Column("task_id", sa.String(64), nullable=False),
        sa.Column("exchange", sa.String(32), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("timeframe", sa.String(16), nullable=False),
        sa.Column("regime", sa.String(32), nullable=False),
        sa.Column("bias", sa.String(32), nullable=False),
        sa.Column("confidence", sa.Numeric(6, 4), nullable=False),
        sa.Column("volatility_level", sa.String(16), nullable=False),
        sa.Column("liquidity_level", sa.String(16), nullable=False),
        sa.Column("key_factors", json_type, nullable=False),
        sa.Column("risk_flags", json_type, nullable=False),
        sa.Column("suggested_strategy_types", json_type, nullable=False),
        sa.Column("raw_payload", json_type, nullable=False),
        sa.Column("created_by_agent", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
    )
    op.create_table(
        "strategy_selection",
        sa.Column("id", pk_type, primary_key=True, autoincrement=True),
        sa.Column("selection_id", sa.String(64), nullable=False, unique=True),
        sa.Column("task_id", sa.String(64), nullable=False),
        sa.Column("analysis_id", sa.String(64), nullable=False),
        sa.Column("selected_strategy_id", sa.String(64), nullable=False),
        sa.Column("candidate_strategies", json_type, nullable=False),
        sa.Column("selection_reason", sa.Text(), nullable=False),
        sa.Column("fit_score", sa.Numeric(6, 4), nullable=False),
        sa.Column("fallback_strategy_id", sa.String(64), nullable=True),
        sa.Column("raw_payload", json_type, nullable=False),
        sa.Column("created_by_agent", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
    )
    op.create_table(
        "audit_decision",
        sa.Column("id", pk_type, primary_key=True, autoincrement=True),
        sa.Column("audit_id", sa.String(64), nullable=False, unique=True),
        sa.Column("task_id", sa.String(64), nullable=False),
        sa.Column("analysis_id", sa.String(64), nullable=False),
        sa.Column("selection_id", sa.String(64), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("risk_level", sa.String(16), nullable=False),
        sa.Column("rejection_reasons", json_type, nullable=False),
        sa.Column("warnings", json_type, nullable=False),
        sa.Column("required_adjustments", json_type, nullable=False),
        sa.Column("approved_order_plan", json_type, nullable=False),
        sa.Column("raw_payload", json_type, nullable=False),
        sa.Column("created_by_agent", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
    )
    op.create_table(
        "execution_order",
        sa.Column("id", pk_type, primary_key=True, autoincrement=True),
        sa.Column("exec_order_id", sa.String(64), nullable=False, unique=True),
        sa.Column("task_id", sa.String(64), nullable=False),
        sa.Column("audit_id", sa.String(64), nullable=False),
        sa.Column("exchange", sa.String(32), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("side", sa.String(16), nullable=False),
        sa.Column("position_side", sa.String(16), nullable=False),
        sa.Column("order_type", sa.String(16), nullable=False),
        sa.Column("execution_mode", sa.String(16), nullable=False),
        sa.Column("price", sa.Numeric(24, 8), nullable=False),
        sa.Column("quantity", sa.Numeric(24, 8), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("exchange_order_id", sa.String(128), nullable=True),
        sa.Column("client_order_id", sa.String(128), nullable=True),
        sa.Column("avg_fill_price", sa.Numeric(24, 8), nullable=True),
        sa.Column("filled_qty", sa.Numeric(24, 8), nullable=False),
        sa.Column("fee", sa.Numeric(24, 8), nullable=False),
        sa.Column("estimated_slippage_bps", sa.Numeric(10, 4), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("placed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("filled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
    )
    op.create_table(
        "task_event_log",
        sa.Column("id", pk_type, primary_key=True, autoincrement=True),
        sa.Column("task_id", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("event_source", sa.String(64), nullable=False),
        sa.Column("event_payload", json_type, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("level", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
    )


def downgrade() -> None:
    for table_name in [
        "task_event_log",
        "execution_order",
        "audit_decision",
        "strategy_selection",
        "analysis_report",
        "strategy_metadata",
        "market_derivatives_metric",
        "market_trade_tick",
        "market_orderbook_snapshot",
        "market_ohlcv",
    ]:
        op.drop_table(table_name)

