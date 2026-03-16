"""phase3 monitor and tooling

Revision ID: 0003_phase3_monitor_and_tooling
Revises: 0002_phase2_backend_hardening
Create Date: 2026-03-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_phase3_monitor_and_tooling"
down_revision = "0002_phase2_backend_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("monitor_snapshot", sa.Column("source_freshness_json", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("monitor_snapshot", sa.Column("suggestions_json", sa.JSON(), nullable=False, server_default="[]"))


def downgrade() -> None:
    op.drop_column("monitor_snapshot", "suggestions_json")
    op.drop_column("monitor_snapshot", "source_freshness_json")
