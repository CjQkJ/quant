"""phase2 backend hardening

Revision ID: 0002_phase2_backend_hardening
Revises: 0001_initial_schema
Create Date: 2026-03-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_phase2_backend_hardening"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    json_type = sa.JSON()
    pk_type = sa.BigInteger().with_variant(sa.Integer(), "sqlite")

    op.add_column("analysis_report", sa.Column("analysis_version", sa.String(32), nullable=False, server_default="analysis.v2"))

    op.add_column("strategy_selection", sa.Column("ranking_version", sa.String(32), nullable=False, server_default="ranking.v2"))
    op.add_column("strategy_selection", sa.Column("selected_strategy_name", sa.String(128), nullable=False, server_default=""))
    op.add_column("strategy_selection", sa.Column("selected_strategy_type", sa.String(64), nullable=False, server_default=""))
    op.add_column("strategy_selection", sa.Column("switch_attempted", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("strategy_selection", sa.Column("cooldown_applied", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("strategy_selection", sa.Column("selection_policy_note", sa.String(64), nullable=False, server_default="normal"))

    op.add_column("audit_decision", sa.Column("strategy_signal_id", sa.String(64), nullable=True))
    op.add_column("audit_decision", sa.Column("risk_policy_version", sa.String(32), nullable=False, server_default="risk-policy.v2"))

    op.add_column("execution_order", sa.Column("strategy_signal_id", sa.String(64), nullable=True))
    op.add_column("execution_order", sa.Column("market_type", sa.String(16), nullable=False, server_default="futures"))
    op.add_column("execution_order", sa.Column("account_mode", sa.String(16), nullable=False, server_default="paper"))
    op.add_column("execution_order", sa.Column("realized_pnl", sa.Numeric(24, 8), nullable=False, server_default="0"))
    op.add_column("execution_order", sa.Column("unrealized_pnl_at_fill", sa.Numeric(24, 8), nullable=False, server_default="0"))

    op.create_table(
        "strategy_signal",
        sa.Column("id", pk_type, primary_key=True, autoincrement=True),
        sa.Column("signal_id", sa.String(64), nullable=False, unique=True),
        sa.Column("task_id", sa.String(64), nullable=False),
        sa.Column("analysis_id", sa.String(64), nullable=False),
        sa.Column("selection_id", sa.String(64), nullable=False),
        sa.Column("strategy_id", sa.String(64), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("timeframe", sa.String(16), nullable=False),
        sa.Column("market_type", sa.String(16), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("strength", sa.Numeric(8, 4), nullable=False),
        sa.Column("target_position_ratio", sa.Numeric(8, 4), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("risk_tags", json_type, nullable=False),
        sa.Column("strategy_runtime_version", sa.String(32), nullable=False),
        sa.Column("raw_payload", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
    )

    op.create_table(
        "paper_account_snapshot",
        sa.Column("id", pk_type, primary_key=True, autoincrement=True),
        sa.Column("snapshot_id", sa.String(64), nullable=False, unique=True),
        sa.Column("task_id", sa.String(64), nullable=True),
        sa.Column("symbol", sa.String(32), nullable=True),
        sa.Column("market_type", sa.String(16), nullable=False),
        sa.Column("account_mode", sa.String(16), nullable=False),
        sa.Column("equity", sa.Numeric(24, 8), nullable=False),
        sa.Column("cash_balance", sa.Numeric(24, 8), nullable=False),
        sa.Column("available_balance", sa.Numeric(24, 8), nullable=False),
        sa.Column("used_margin", sa.Numeric(24, 8), nullable=False),
        sa.Column("realized_pnl", sa.Numeric(24, 8), nullable=False),
        sa.Column("unrealized_pnl", sa.Numeric(24, 8), nullable=False),
        sa.Column("avg_slippage_bps", sa.Numeric(10, 4), nullable=False),
        sa.Column("positions_json", json_type, nullable=False),
        sa.Column("raw_payload", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
    )

    op.create_table(
        "monitor_snapshot",
        sa.Column("id", pk_type, primary_key=True, autoincrement=True),
        sa.Column("snapshot_id", sa.String(64), nullable=False, unique=True),
        sa.Column("task_id", sa.String(64), nullable=True),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("risk_policy_version", sa.String(32), nullable=False),
        sa.Column("system_status", sa.String(16), nullable=False),
        sa.Column("account_status_json", json_type, nullable=False),
        sa.Column("risk_metrics_json", json_type, nullable=False),
        sa.Column("alerts_json", json_type, nullable=False),
        sa.Column("actions_json", json_type, nullable=False),
        sa.Column("kill_switch", sa.Boolean(), nullable=False),
        sa.Column("raw_payload", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
    )

    op.create_table(
        "replay_run",
        sa.Column("id", pk_type, primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(64), nullable=False, unique=True),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("timeframe", sa.String(16), nullable=False),
        sa.Column("fixture_name", sa.String(128), nullable=False),
        sa.Column("analysis_version", sa.String(32), nullable=False),
        sa.Column("ranking_version", sa.String(32), nullable=False),
        sa.Column("risk_policy_version", sa.String(32), nullable=False),
        sa.Column("strategy_runtime_version", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary_json", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
    )

    op.create_table(
        "replay_cycle_result",
        sa.Column("id", pk_type, primary_key=True, autoincrement=True),
        sa.Column("cycle_id", sa.String(64), nullable=False, unique=True),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("task_id", sa.String(64), nullable=False),
        sa.Column("cycle_index", sa.Integer(), nullable=False),
        sa.Column("bar_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("selected_strategy_id", sa.String(64), nullable=False),
        sa.Column("strategy_signal_action", sa.String(16), nullable=False),
        sa.Column("strategy_signal_direction", sa.String(16), nullable=False),
        sa.Column("audit_decision", sa.String(32), nullable=False),
        sa.Column("execution_status", sa.String(32), nullable=False),
        sa.Column("switch_attempted", sa.Boolean(), nullable=False),
        sa.Column("cooldown_applied", sa.Boolean(), nullable=False),
        sa.Column("account_snapshot_json", json_type, nullable=False),
        sa.Column("raw_payload", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
    )


def downgrade() -> None:
    for table_name in [
        "replay_cycle_result",
        "replay_run",
        "monitor_snapshot",
        "paper_account_snapshot",
        "strategy_signal",
    ]:
        op.drop_table(table_name)

    op.drop_column("execution_order", "unrealized_pnl_at_fill")
    op.drop_column("execution_order", "realized_pnl")
    op.drop_column("execution_order", "account_mode")
    op.drop_column("execution_order", "market_type")
    op.drop_column("execution_order", "strategy_signal_id")

    op.drop_column("audit_decision", "risk_policy_version")
    op.drop_column("audit_decision", "strategy_signal_id")

    op.drop_column("strategy_selection", "selection_policy_note")
    op.drop_column("strategy_selection", "cooldown_applied")
    op.drop_column("strategy_selection", "switch_attempted")
    op.drop_column("strategy_selection", "selected_strategy_type")
    op.drop_column("strategy_selection", "selected_strategy_name")
    op.drop_column("strategy_selection", "ranking_version")

    op.drop_column("analysis_report", "analysis_version")
