# 项目现状导览

这份文档只回答三个问题：

1. 现在这个项目已经能干什么
2. 你应该从哪里看懂它
3. 还差哪些关键环节没补完

## 一句话结论

`quant-system` 现在已经是一个能跑通完整模拟闭环的后端原型，不是空壳，但也还不是能上实盘的成品。

它当前能跑通的流程是：

```text
市场数据
  -> 分析
  -> 选策略
  -> 策略运行信号
  -> 审核
  -> 模拟执行
  -> 监控
  -> 事件日志
```

## 一张图看懂当前结构

```text
Binance 数据 / 演示数据
  -> apps/market_data
     负责标准化 OHLCV、订单簿、Funding、OI
  -> apps/analysis_engine
     生成市场状态、方向偏向、置信度、风险标记
  -> apps/strategy_registry
     从预置策略库里挑选候选策略
  -> apps/risk_engine
     做审核、检查仓位、检查 kill switch
  -> apps/execution_engine
     在 paper trading 模式下生成并成交模拟订单
  -> apps/agent_orchestrator
     把五个环节串起来，形成一次完整 run cycle
  -> shared/models/tables.py
     把结果写入数据库和事件日志
```

## 最重要的文件怎么对应

- [apps/agent_orchestrator/main.py](../../apps/agent_orchestrator/main.py)
  这是总入口。现在系统能不能跑通，主要看这里。
- [apps/analysis_engine/services/signal_summary_service.py](../../apps/analysis_engine/services/signal_summary_service.py)
  这里负责把市场数据整理成“分析结果”。
- [apps/strategy_registry/services/registry_service.py](../../apps/strategy_registry/services/registry_service.py)
  这里定义并写入当前的 4 个预置策略。
- [apps/strategy_runtime/services/runtime_service.py](../../apps/strategy_runtime/services/runtime_service.py)
  这里让被选中的策略真正输出 `entry / reduce / exit / hold / no_trade`。
- [apps/risk_engine/services/audit_service.py](../../apps/risk_engine/services/audit_service.py)
  这里决定本轮是 `approve`、`reject`、`downgrade` 还是 `observe_only`。
- [apps/execution_engine/services/order_executor.py](../../apps/execution_engine/services/order_executor.py)
  这里做模拟成交，不会真实下单。
- [shared/models/tables.py](../../shared/models/tables.py)
  这里是第一阶段核心表和第二阶段新增的 replay / signal / snapshot 表。
- [scripts/demo_cycle.py](../../scripts/demo_cycle.py)
  这是最适合看“项目现在会做什么”的演示脚本。
- [scripts/replay_events.py](../../scripts/replay_events.py)
  这是最适合看“这套流程能不能反复跑”的回放脚本。

## 你现在最应该怎么体验

### 1. 初始化

```bash
python scripts/init_db.py
python scripts/seed_strategies.py
python scripts/startup_check.py
```

你会看到：

- 数据库能连通
- 默认策略能写入
- 状态存储可用

### 2. 直接跑一次演示闭环

```bash
python scripts/demo_cycle.py
```

默认是 `trend` 模式，通常会看到类似结果：

```text
演示完成
流程概览
- market_trigger <- system
- analysis_done <- analyst_agent
- strategy_selected <- selector_agent
- audit_done <- auditor_agent
- execution_done <- executor_agent
- monitor_done <- monitor_agent

分析结果
- 方向偏向: neutral_to_long

策略与审核
- 审核结论: approve

执行与监控
- 执行状态: filled
```

这表示：

- 系统已经完成了一整轮判断
- 它不是只做分析，而是真的走到了模拟成交
- 五个 agent 的工作顺序已经连起来了

### 3. 看一个更保守的场景

```bash
python scripts/demo_cycle.py --mode low_confidence
```

这个场景更适合看系统“选择不交易或降级”的路径。

### 4. 跑回放

```bash
python scripts/replay_events.py
```

这一步说明系统不只是能跑一次，还能按历史 bar 连续跑多轮，并输出策略切换、冷却命中和执行结果统计。

### 5. 看风控拦截

```bash
python scripts/demo_cycle.py --kill-switch-on
```

这一步最直观地展示：

- 风控开关被打开后
- 审核阶段会拒绝
- 执行阶段会跳过
- 系统不会继续做 paper fill

## 当前已经完成的东西

- 能初始化数据库并写入 10 张核心表
- 能写入 4 个默认策略
- 能输出结构化分析结果
- 能完成结构化策略选择
- 能输出结构化策略运行信号
- 能完成结构化审核
- 能做 paper trading 模拟执行
- 能记录任务事件日志
- 能在监控阶段检查 kill switch
- 能做带版本号和统计的基础回放
- 能通过单元测试和集成测试

## 当前还没完成的东西

- 还没有真实交易执行
- 还没有多交易所、多币种支持
- 还没有把每个服务都拆成独立 API 服务
- 还没有前端控制台
- 还没有真正接上 OpenClaw 的完整运行链路
- 市场数据采集还更像“原型服务”，不是长期运行的生产采集器
- 部署、告警、观测、恢复策略还需要继续补齐

## 现阶段最值得优先改进的地方

### 第一优先级

- 把 `market_data / analysis / risk / execution` 各自补成清晰的 API 入口
- 把演示数据和真实 Binance 数据采集彻底分开
- 补完整的启动脚本和开发环境说明

### 第二优先级

- 增强回放，输出更清晰的策略切换和执行统计
- 增加更多审核规则和更细的风控参数
- 增加更直观的状态查询接口

### 第三优先级

- 对接 OpenClaw 工具注册
- 增加控制台页面
- 为后续实盘做权限隔离和审计加固

## 最后怎么判断它现在处在哪个阶段

如果你问“这是不是成品”，答案是否定的。

如果你问“这是不是已经有真实可看的效果”，答案是肯定的。

当前最准确的定位是：

一个已经能跑通第一阶段核心闭环的可运行后端原型。
