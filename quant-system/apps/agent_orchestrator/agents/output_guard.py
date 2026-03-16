"""Agent 输出校验守卫。"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from apps.agent_orchestrator.services.task_event_logger import TaskEventLogger
from shared.schemas.base import BaseSchema


class AgentOutputGuard:
    """校验 agent 输出，并在无效时记录事件日志。"""

    def __init__(self, event_logger: TaskEventLogger | None = None) -> None:
        self.event_logger = event_logger or TaskEventLogger()

    def validate(
        self,
        session: Session,
        task_id: str,
        agent_name: str,
        expected_schema: type[BaseSchema],
        output: BaseSchema | dict[str, Any],
        *,
        source_kind: str = "backend",
    ) -> BaseSchema:
        try:
            if isinstance(output, expected_schema):
                return output
            if isinstance(output, BaseSchema):
                return expected_schema.model_validate(output.model_dump(mode="json"))
            return expected_schema.model_validate(output)
        except ValidationError as exc:
            raw_output: Any
            if isinstance(output, BaseSchema):
                raw_output = output.model_dump(mode="json")
            else:
                raw_output = output
            event_type = "openclaw_agent_output_invalid" if source_kind == "openclaw" else "agent_output_invalid"
            self.event_logger.log(
                session,
                task_id=task_id,
                event_type=event_type,
                source=agent_name,
                payload={
                    "expected_schema": expected_schema.__name__,
                    "source_kind": source_kind,
                    "errors": exc.errors(),
                    "raw_output": raw_output,
                },
                message=f"{agent_name} 输出不符合 {expected_schema.__name__}",
                level="error",
            )
            raise ValueError(f"{agent_name} 输出校验失败") from exc
