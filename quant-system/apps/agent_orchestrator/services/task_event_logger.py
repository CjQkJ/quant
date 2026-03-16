"""任务事件日志服务。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from shared.models.tables import TaskEventLog


class TaskEventLogger:
    """统一写入任务事件日志。"""

    def log(
        self,
        session: Session,
        task_id: str,
        event_type: str,
        source: str,
        payload: dict[str, Any],
        message: str,
        level: str = "info",
    ) -> None:
        session.add(
            TaskEventLog(
                task_id=task_id,
                event_type=event_type,
                event_source=source,
                event_payload=payload,
                message=message,
                level=level,
            )
        )
        session.flush()
