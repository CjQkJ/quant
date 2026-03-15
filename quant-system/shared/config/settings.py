"""项目配置。"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """统一配置入口。"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    database_url: str = Field(
        default="sqlite+pysqlite:///./quant_system.db",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    default_exchange: str = Field(default="binance", alias="DEFAULT_EXCHANGE")
    default_symbol: str = Field(default="BTCUSDT", alias="DEFAULT_SYMBOL")
    primary_timeframe: str = Field(default="5m", alias="PRIMARY_TIMEFRAME")
    aux_timeframe: str = Field(default="15m", alias="AUX_TIMEFRAME")
    paper_initial_equity: float = Field(default=10000.0, alias="PAPER_INITIAL_EQUITY")
    maker_fee_bps: float = Field(default=2.0, alias="MAKER_FEE_BPS")
    taker_fee_bps: float = Field(default=4.0, alias="TAKER_FEE_BPS")
    slippage_bps: float = Field(default=3.0, alias="SLIPPAGE_BPS")
    binance_proxy: str | None = Field(default=None, alias="BINANCE_PROXY")
    openclaw_read_only: bool = Field(default=True, alias="OPENCLAW_READ_ONLY")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

