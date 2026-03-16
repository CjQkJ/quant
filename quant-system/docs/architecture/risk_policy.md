# 风险策略

第二阶段风控参数统一收口到 `shared/config/risk_policy.json`，并通过 `risk_policy_version` 贯穿 replay、audit、monitor 和 orchestrator。

## kill switch

- 以 Redis 为单一事实来源
- 审核前检查一次
- 执行前再检查一次
- 超过暴露或回撤阈值时由监控服务触发

## 审核规则

- `reject`：kill switch、回撤超限、暴露超限、策略不适用、低流动性入场、事件风险阻断
- `observe_only`：低置信度、防御策略、`no_trade / hold` 信号
- `downgrade`：中等风险、高波动环境、`reduce` 信号
- `approve`：其余正常场景

## 默认参数

- `drawdown_limit = 0.08`
- `exposure_limit = 0.30`
- `observe_confidence_lt = 0.40`
- `downgrade_confidence_lt = 0.60`
- `strategy_switch_cooldown_seconds = 900`
