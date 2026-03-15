"""启动前检查。"""

from sqlalchemy import text

from shared.config.settings import get_settings
from shared.db.session import get_engine
from shared.utils.state_store import InMemoryStateStore


def main() -> None:
    settings = get_settings()
    print(f"APP_ENV={settings.app_env}")
    print(f"DEFAULT_SYMBOL={settings.default_symbol}")
    with get_engine().connect() as conn:
        conn.execute(text("SELECT 1"))
    print("数据库连接正常")
    store = InMemoryStateStore()
    store.set_bool("startup:ok", True)
    print("状态存储检查正常")


if __name__ == "__main__":
    main()

