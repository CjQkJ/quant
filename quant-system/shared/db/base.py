"""数据库基础定义。"""

from __future__ import annotations

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


JsonDocument = JSON().with_variant(JSONB, "postgresql")

