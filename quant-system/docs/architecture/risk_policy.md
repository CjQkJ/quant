# 风险策略

## kill switch

- 以 Redis 为单一事实来源
- 审核前检查一次
- 执行前再检查一次
- 超过暴露或回撤阈值时由监控服务触发

## 审核规则

- `reject`：kill switch、回撤超限、暴露超限、策略不适用
- `observe_only`：低置信度或防御策略
- `downgrade`：中等风险或高波动环境
- `approve`：其余正常场景

