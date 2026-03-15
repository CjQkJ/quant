# quant-system

第一阶段多智能体交易闭环系统，目标是先跑通 `Binance + BTCUSDT + paper trading` 的最小可运行版本，而不是直接追求收益最大化。

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

- [docs/runbooks/project_tour.md](E:/quant/quant-system/docs/runbooks/project_tour.md)

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
- 分析、选策略、审核、paper execution、监控的结构化输出
- Redis `kill switch` 与 paper 账户状态存储
- 本地 orchestrator 全流程
- Replay 驱动与测试样例
