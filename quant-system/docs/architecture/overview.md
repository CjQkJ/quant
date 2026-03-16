# 分阶段概览

当前仓库仍保持第一阶段边界：`Binance + BTCUSDT + 5m/15m + paper trading`。

在这个范围内，代码已经推进到第三阶段骨架：

- 第一阶段：跑通多智能体交易闭环
- 第二阶段：补 replay、风控参数化、paper portfolio realism
- 第三阶段：补受控工具执行、策略 runtime 插件、旁路 agent 和 OpenClaw workspace 模板

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
- OpenClaw 首批 `5+1` workspace 模板已准备好

## 第一阶段不做

- 多交易所
- 多币种
- 高频交易
- 自动写策略
- 无人值守实盘
- 复杂新闻、链上和情绪融合
