"""工具执行器。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from apps.agent_orchestrator.services.task_event_logger import TaskEventLogger
from apps.agent_orchestrator.tools.schema_guard import SchemaGuard, SchemaGuardError
from apps.agent_orchestrator.tools.tool_registry import ToolRegistry, build_tool_registry
from shared.schemas.base import BaseSchema
from shared.utils.ids import new_task_id


class ToolExecutor:
    """统一执行受控工具。"""

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        schema_guard: SchemaGuard | None = None,
        event_logger: TaskEventLogger | None = None,
    ) -> None:
        self.registry = registry or build_tool_registry()
        self.schema_guard = schema_guard or SchemaGuard()
        self.event_logger = event_logger or TaskEventLogger()

    def execute(
        self,
        session: Session,
        role: str,
        tool_name: str,
        payload: dict[str, Any] | BaseSchema,
        *,
        task_id: str | None = None,
    ) -> tuple[str, BaseSchema]:
        request_task_id = task_id or new_task_id()
        tool = self.registry.get(tool_name)
        if tool is None or role not in tool.roles:
            self.event_logger.log(
                session,
                task_id=request_task_id,
                event_type="tool_acl_denied",
                source=role,
                payload={"tool_name": tool_name, "role": role},
                message=f"{role} 无权调用工具 {tool_name}",
                level="error",
            )
            raise PermissionError(f"{role} 无权调用工具 {tool_name}")

        try:
            validated_input = self.schema_guard.validate(payload, tool.input_model, phase="input")
        except SchemaGuardError as exc:
            self.event_logger.log(
                session,
                task_id=request_task_id,
                event_type="tool_input_invalid",
                source=tool_name,
                payload={
                    "role": role,
                    "schema": exc.schema_name,
                    "errors": exc.errors,
                    "raw_payload": exc.raw_payload,
                },
                message=f"{tool_name} 输入不符合 {exc.schema_name}",
                level="error",
            )
            raise

        try:
            raw_output = tool.handler(session, validated_input)
        except Exception as exc:
            self.event_logger.log(
                session,
                task_id=request_task_id,
                event_type="tool_runtime_failed",
                source=tool_name,
                payload={"role": role, "error": str(exc)},
                message=f"{tool_name} 执行失败",
                level="error",
            )
            raise

        try:
            validated_output = self.schema_guard.validate(raw_output, tool.output_model, phase="output")
        except SchemaGuardError as exc:
            self.event_logger.log(
                session,
                task_id=request_task_id,
                event_type="tool_output_invalid",
                source=tool_name,
                payload={
                    "role": role,
                    "schema": exc.schema_name,
                    "errors": exc.errors,
                    "raw_payload": exc.raw_payload,
                },
                message=f"{tool_name} 输出不符合 {exc.schema_name}",
                level="error",
            )
            raise

        self.event_logger.log(
            session,
            task_id=request_task_id,
            event_type="tool_executed",
            source=tool_name,
            payload={
                "role": role,
                "tool_name": tool_name,
                "input_schema": tool.input_model.__name__,
                "output_schema": tool.output_model.__name__,
            },
            message=f"{role} 已调用工具 {tool_name}",
        )
        return request_task_id, validated_output
