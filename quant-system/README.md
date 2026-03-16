# quant-system

当前仓库已经从第一阶段原型推进到第三阶段骨架：先跑通 `Binance + BTCUSDT + paper trading` 的最小可运行版本，再补 replay、受控工具执行、策略运行时插件和 OpenClaw 工作区模板。

## 第一阶段边界

- 交易所只做 `Binance`
- 交易对只做 `BTCUSDT`
- 主周期 `5m`，辅助周期 `15m`
- 策略由人工预置，智能体只负责选择和审核
- 执行模式只做 `paper trading`
- OpenClaw 只做编排、协作和控制台，不直接拥有真实下单权限

## 快速开始

```bash
python -m pip install -e .[dev]
docker compose up -d postgres redis
python scripts/init_db.py
python scripts/seed_strategies.py
python -m uvicorn apps.agent_orchestrator.main:app --reload
```

## 直观体验

如果你想先看“这个项目现在到底会做什么”，先跑这几条：

```bash
python scripts/startup_check.py
python scripts/demo_cycle.py
python scripts/demo_cycle.py --mode low_confidence
python scripts/demo_cycle.py --kill-switch-on
python scripts/replay_events.py
```

更适合快速看懂项目现状的说明见：

- [docs/runbooks/project_tour.md](docs/runbooks/project_tour.md)

## 目录

```text
quant-system/
├─ apps/
│  ├─ market_data/
│  ├─ strategy_registry/
│  ├─ analysis_engine/
│  ├─ risk_engine/
│  ├─ execution_engine/
│  └─ agent_orchestrator/
├─ shared/
├─ docs/
├─ scripts/
└─ tests/
```

## 已实现内容

- 10 张核心表的 SQLAlchemy 模型与 Alembic 初始迁移
- Binance REST/WS 客户端骨架
- 市场数据标准化与落库服务
- 分析、选策略、策略运行信号、审核、paper execution、监控的结构化输出
- Redis `kill switch` 与 paper 账户状态存储
- 本地 orchestrator 全流程
- Replay 驱动、版本控制层、ReplayEvaluator/ReplayReporter 与测试样例
- `tool_registry -> schema_guard -> tool_executor` 的受控工具执行层
- `strategy_runtime` 插件化注册表与独立策略 runtime
- OpenClaw 首批 `5+1` workspace 模板和部署脚本，见 [openclaw/README.md](openclaw/README.md) 与 [scripts/deploy_openclaw_workspaces.py](scripts/deploy_openclaw_workspaces.py)

## 运行期文件

- 默认 SQLite 演示库和脚本输出都写到 `.runtime/`
- 仓库不再保留演示 `.db` 文件
- 固定回放样本只放在 `tests/fixtures/`
