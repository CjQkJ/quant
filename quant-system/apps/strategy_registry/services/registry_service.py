"""策略注册服务。"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.strategy_registry.schemas.strategy import StrategyMetadataSchema
from shared.models.tables import StrategyMetadata


DEFAULT_STRATEGIES = [
    StrategyMetadataSchema(
        strategy_id="trend_long_btc_5m_v1",
        strategy_name="BTC 5m 趋势跟随",
        strategy_type="trend_following",
        description="适用于趋势行情的低杠杆做多策略。",
        supported_exchange="binance",
        supported_symbol="BTCUSDT",
        supported_timeframe="5m",
        market_regime_fit=["trend"],
        directional_fit=["long", "neutral_to_long"],
        risk_level="medium",
        max_position_ratio=0.15,
        leverage_allowed=False,
        cooldown_seconds=900,
        disable_conditions=["kill_switch", "high_drawdown"],
        priority=8,
    ),
    StrategyMetadataSchema(
        strategy_id="mr_btc_5m_v1",
        strategy_name="BTC 5m 均值回归",
        strategy_type="mean_reversion",
        description="适用于箱体或震荡行情。",
        supported_exchange="binance",
        supported_symbol="BTCUSDT",
        supported_timeframe="5m",
        market_regime_fit=["range"],
        directional_fit=["neutral", "neutral_to_short", "neutral_to_long"],
        risk_level="medium",
        max_position_ratio=0.12,
        leverage_allowed=False,
        cooldown_seconds=600,
        disable_conditions=["kill_switch"],
        priority=9,
    ),
    StrategyMetadataSchema(
        strategy_id="breakout_filter_btc_5m_v1",
        strategy_name="BTC 5m 突破过滤",
        strategy_type="breakout_filter",
        description="适用于事件驱动和高波动阶段。",
        supported_exchange="binance",
        supported_symbol="BTCUSDT",
        supported_timeframe="5m",
        market_regime_fit=["event", "high_vol", "trend"],
        directional_fit=["long", "short", "neutral_to_short", "neutral_to_long"],
        risk_level="high",
        max_position_ratio=0.08,
        leverage_allowed=False,
        cooldown_seconds=1200,
        disable_conditions=["kill_switch", "high_spread"],
        priority=6,
    ),
    StrategyMetadataSchema(
        strategy_id="defensive_no_trade_btc_5m_v1",
        strategy_name="BTC 5m 防御观察",
        strategy_type="defensive",
        description="用于低置信度或高风险场景，优先观察。",
        supported_exchange="binance",
        supported_symbol="BTCUSDT",
        supported_timeframe="5m",
        market_regime_fit=["trend", "range", "event", "high_vol"],
        directional_fit=["long", "short", "neutral", "neutral_to_short", "neutral_to_long"],
        risk_level="low",
        max_position_ratio=0.0,
        leverage_allowed=False,
        cooldown_seconds=300,
        disable_conditions=None,
        priority=5,
    ),
]


class RegistryService:
    def seed_default_strategies(self, session: Session) -> list[StrategyMetadata]:
        rows: list[StrategyMetadata] = []
        for item in DEFAULT_STRATEGIES:
            stmt = select(StrategyMetadata).where(StrategyMetadata.strategy_id == item.strategy_id)
            row = session.scalar(stmt)
            if row is None:
                row = StrategyMetadata(
                    strategy_id=item.strategy_id,
                    strategy_name=item.strategy_name,
                    strategy_type=item.strategy_type,
                    description=item.description,
                    supported_exchange=item.supported_exchange,
                    supported_symbol=item.supported_symbol,
                    supported_timeframe=item.supported_timeframe,
                    market_regime_fit=item.market_regime_fit,
                    directional_fit=item.directional_fit,
                    risk_level=item.risk_level,
                    max_position_ratio=Decimal(str(item.max_position_ratio)),
                    leverage_allowed=item.leverage_allowed,
                    cooldown_seconds=item.cooldown_seconds,
                    disable_conditions=item.disable_conditions,
                    priority=item.priority,
                    enabled=item.enabled,
                    version=item.version,
                )
                session.add(row)
            rows.append(row)
        session.flush()
        return rows

    def list_enabled(self, session: Session, symbol: str, timeframe: str) -> list[StrategyMetadata]:
        stmt = select(StrategyMetadata).where(
            StrategyMetadata.enabled.is_(True),
            StrategyMetadata.supported_symbol == symbol,
            StrategyMetadata.supported_timeframe == timeframe,
        )
        return list(session.scalars(stmt).all())

