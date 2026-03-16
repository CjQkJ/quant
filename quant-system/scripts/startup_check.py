"""启动前检查。"""

from sqlalchemy import text

from shared.config.risk_policy import get_risk_policy
from shared.config.settings import get_settings
from shared.db.session import get_engine
from shared.utils.state_store import InMemoryStateStore


def main() -> None:
    settings = get_settings()
    policy = get_risk_policy()
    print(f"APP_ENV={settings.app_env}")
    print(f"DEFAULT_SYMBOL={settings.default_symbol}")
    print(f"DEFAULT_MARKET_TYPE={settings.default_market_type}")
    print(f"DEFAULT_ACCOUNT_MODE={settings.default_account_mode}")
    print(f"RUNTIME_DIR={settings.runtime_dir}")
    with get_engine().connect() as conn:
        conn.execute(text("SELECT 1"))
    print("数据库连接正常")
    store = InMemoryStateStore()
    store.set_bool("startup:ok", True)
    print("状态存储检查正常")
    print(f"风控策略版本={policy.version}")
    print(f"内部 API 允许主机={','.join(sorted(settings.internal_api_host_set()))}")


if __name__ == "__main__":
    main()
