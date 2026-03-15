"""业务 ID 生成工具。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


def _timestamp_token() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def build_id(prefix: str) -> str:
    return f"{prefix}_{_timestamp_token()}_{uuid.uuid4().hex[:8]}"


def new_task_id() -> str:
    return build_id("task")


def new_analysis_id() -> str:
    return build_id("analysis")


def new_selection_id() -> str:
    return build_id("selection")


def new_audit_id() -> str:
    return build_id("audit")


def new_execution_id() -> str:
    return build_id("exec")
