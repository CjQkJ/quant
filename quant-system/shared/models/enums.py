"""枚举定义。"""

from enum import Enum


class StringEnum(str, Enum):
    pass


class MarketRegime(StringEnum):
    TREND = "trend"
    RANGE = "range"
    EVENT = "event"
    HIGH_VOL = "high_vol"


class DirectionalBias(StringEnum):
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"
    NEUTRAL_TO_SHORT = "neutral_to_short"
    NEUTRAL_TO_LONG = "neutral_to_long"


class RiskLevel(StringEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditDecisionType(StringEnum):
    APPROVE = "approve"
    REJECT = "reject"
    DOWNGRADE = "downgrade"
    OBSERVE_ONLY = "observe_only"


class OrderStatus(StringEnum):
    PENDING = "pending"
    PLACED = "placed"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionMode(StringEnum):
    PAPER = "paper"
    LIVE = "live"


class SystemStatus(StringEnum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    HALTED = "halted"
