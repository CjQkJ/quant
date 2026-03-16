"""风险策略配置加载。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import Field

from shared.config.settings import get_settings
from shared.schemas.base import BaseSchema


class RiskPolicyConfig(BaseSchema):
    """统一的风控参数。"""

    version: str
    drawdown_limit: float = Field(gt=0)
    exposure_limit: float = Field(gt=0)
    observe_confidence_lt: float = Field(ge=0, le=1)
    downgrade_confidence_lt: float = Field(ge=0, le=1)
    high_volatility_levels: list[str]
    low_liquidity_levels: list[str]
    event_risk_blocklist: list[str]
    default_max_position_ratio: float = Field(ge=0, le=1)
    downgraded_max_position_ratio: float = Field(ge=0, le=1)
    strategy_switch_cooldown_seconds: int = Field(ge=0)


def _load_policy_dict() -> dict:
    settings = get_settings()
    policy_path = Path(settings.risk_policy_path)
    data = json.loads(policy_path.read_text(encoding="utf-8"))
    if settings.risk_policy_overrides_json:
        data.update(json.loads(settings.risk_policy_overrides_json))
    return data


@lru_cache(maxsize=1)
def get_risk_policy() -> RiskPolicyConfig:
    """获取统一风控策略。"""

    return RiskPolicyConfig.model_validate(_load_policy_dict())
