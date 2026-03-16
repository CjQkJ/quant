"""项目配置。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """统一配置入口。"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    runtime_dir: str = Field(default=".runtime", alias="RUNTIME_DIR")
    database_url: str = Field(
        default="sqlite+pysqlite:///./.runtime/quant_system.db",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    default_exchange: str = Field(default="binance", alias="DEFAULT_EXCHANGE")
    default_symbol: str = Field(default="BTCUSDT", alias="DEFAULT_SYMBOL")
    default_market_type: str = Field(default="futures", alias="DEFAULT_MARKET_TYPE")
    default_account_mode: str = Field(default="paper", alias="DEFAULT_ACCOUNT_MODE")
    primary_timeframe: str = Field(default="5m", alias="PRIMARY_TIMEFRAME")
    aux_timeframe: str = Field(default="15m", alias="AUX_TIMEFRAME")
    paper_initial_equity: float = Field(default=10000.0, alias="PAPER_INITIAL_EQUITY")
    paper_initial_margin_ratio: float = Field(default=0.1, alias="PAPER_INITIAL_MARGIN_RATIO")
    maker_fee_bps: float = Field(default=2.0, alias="MAKER_FEE_BPS")
    taker_fee_bps: float = Field(default=4.0, alias="TAKER_FEE_BPS")
    slippage_bps: float = Field(default=3.0, alias="SLIPPAGE_BPS")
    binance_proxy: str | None = Field(default=None, alias="BINANCE_PROXY")
    openclaw_read_only: bool = Field(default=True, alias="OPENCLAW_READ_ONLY")
    risk_policy_path: str = Field(default="shared/config/risk_policy.json", alias="RISK_POLICY_PATH")
    risk_policy_overrides_json: str | None = Field(default=None, alias="RISK_POLICY_OVERRIDES_JSON")
    internal_api_allowed_hosts: str = Field(
        default="127.0.0.1,localhost,testclient",
        alias="INTERNAL_API_ALLOWED_HOSTS",
    )
    allow_remote_internal_api: bool = Field(default=False, alias="ALLOW_REMOTE_INTERNAL_API")
    enable_live_execution: bool = Field(default=False, alias="ENABLE_LIVE_EXECUTION")

    def runtime_path(self, *parts: str) -> Path:
        """返回运行期目录下的路径，并确保目录存在。"""

        base = Path(self.runtime_dir)
        base.mkdir(parents=True, exist_ok=True)
        path = base.joinpath(*parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def internal_api_host_set(self) -> set[str]:
        """解析内部 API 允许访问的主机列表。"""

        return {item.strip() for item in self.internal_api_allowed_hosts.split(",") if item.strip()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
