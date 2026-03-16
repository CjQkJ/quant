"""初始化数据库。"""

from shared.config.settings import get_settings
from shared.db.session import init_db


if __name__ == "__main__":
    init_db()
    print(f"数据库初始化完成: {get_settings().database_url}")
