"""工具输入输出 schema 守卫。"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from shared.schemas.base import BaseSchema


class SchemaGuardError(ValueError):
    def __init__(self, phase: str, schema_name: str, errors: list[dict[str, Any]], raw_payload: Any) -> None:
        self.phase = phase
        self.schema_name = schema_name
        self.errors = errors
        self.raw_payload = raw_payload
        super().__init__(f"{phase} schema 校验失败: {schema_name}")


class SchemaGuard:
    def validate(self, payload: BaseSchema | dict[str, Any], schema: type[BaseSchema], *, phase: str) -> BaseSchema:
        try:
            if isinstance(payload, schema):
                return payload
            if isinstance(payload, BaseSchema):
                return schema.model_validate(payload.model_dump(mode="json"))
            return schema.model_validate(payload)
        except ValidationError as exc:
            if isinstance(payload, BaseSchema):
                raw_payload: Any = payload.model_dump(mode="json")
            else:
                raw_payload = payload
            raise SchemaGuardError(phase=phase, schema_name=schema.__name__, errors=exc.errors(), raw_payload=raw_payload) from exc
