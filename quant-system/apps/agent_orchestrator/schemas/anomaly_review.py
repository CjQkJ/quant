"""异常复盘结构。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from shared.schemas.base import BaseSchema


class AnomalyReviewerInput(BaseSchema):
    task_id: str
    symbol: str = "BTCUSDT"
    lookback_limit: int = Field(default=20, ge=1, le=100)
    access_mode: Literal["read_only"] = "read_only"


class ReviewedEvent(BaseSchema):
    event_type: str
    event_source: str
    level: str
    message: str
    created_at: datetime


class AnomalyReviewerOutput(BaseSchema):
    review_id: str
    review_time: datetime
    task_id: str
    symbol: str
    access_mode: Literal["read_only"] = "read_only"
    event_count: int
    suspected_stage: str
    summary: str
    recommended_next_steps: list[str]
    reviewed_events: list[ReviewedEvent]
