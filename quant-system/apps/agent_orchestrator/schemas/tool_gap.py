"""工具缺口报告结构。"""

from __future__ import annotations

from datetime import datetime

from shared.schemas.base import BaseSchema


class ToolGapItem(BaseSchema):
    code: str
    count: int
    recommendation: str


class ToolGapInput(BaseSchema):
    lookback_limit: int = 100


class ToolGapOutput(BaseSchema):
    report_id: str
    report_time: datetime
    lookback_limit: int
    summary: str
    gap_items: list[ToolGapItem]
