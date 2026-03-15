# 第一阶段概览

第一阶段只做 `Binance + BTCUSDT + 5m/15m + paper trading`，目标是跑通多智能体交易闭环。

## 第一阶段完成定义

- 数据采集稳定
- 能输出 `analysis_report`
- 能输出 `strategy_selection`
- 能输出 `audit_decision`
- 能进行 `paper execution`
- 能记录 `task_event_log`
- 能运行 `monitor cycle`
- 能触发 `kill switch`
- 能通过 orchestrator 跑完整闭环
- OpenClaw 能接入主要 agent 工作流

## 第一阶段不做

- 多交易所
- 多币种
- 高频交易
- 自动写策略
- 无人值守实盘
- 复杂新闻、链上和情绪融合

