"""初始化数据库。"""

from shared.db.session import init_db


if __name__ == "__main__":
    init_db()
    print("数据库初始化完成")

