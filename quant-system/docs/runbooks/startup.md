# 启动 Runbook

1. 安装依赖：`python -m pip install -e .[dev]`
2. 启动基础设施：`docker compose up -d postgres redis`
3. 初始化数据库：`python scripts/init_db.py`
4. 写入默认策略：`python scripts/seed_strategies.py`
5. 运行启动检查：`python scripts/startup_check.py`
6. 如需看最小闭环：`python scripts/demo_cycle.py`
7. 启动 API：`python -m uvicorn apps.agent_orchestrator.main:app --reload`

补充说明：

- 默认 SQLite 运行文件会写到 `.runtime/`
- 内部控制 API 默认只允许本机或内网访问
- `live execution` 相关端点默认关闭
