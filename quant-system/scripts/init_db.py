"""初始化数据库。"""

from alembic import command
from alembic.config import Config

from shared.config.settings import get_settings


if __name__ == "__main__":
    command.upgrade(Config("alembic.ini"), "head")
    print(f"数据库初始化完成: {get_settings().database_url}")
