# 第三阶段实施计划：双层系统稳态落地版

## 摘要
第三阶段不再继续“补单点功能”，而是把当前 `quant-system` 推进成两层并进的受控系统：

- 主链岗位系统：`analyst -> selector -> auditor -> executor -> monitor`
- 旁路探索系统：`replay_planner / anomaly_reviewer / tool_gap`

本阶段仍坚持：
- 单仓模块化，不拆多服务集群
- 主市场仍是 `Binance Futures + paper`
- OpenClaw 是编排与增益层，不替代本地规则引擎
- `live execution` 默认关闭，不作为本阶段交付

实施顺序按“先铺调用轨道，再放开岗位自主性”执行，避免先长出不受控 agent 调用。

## 关键改造

### 第 1 周：仓库收口 + Replay 基线固化
- 清理根目录遗留 `.db`，统一 `.runtime/` 为唯一运行时输出目录。
- README、runbook、脚本行为统一，所有示例只保留三条主路径：最小闭环、回放、风险拦截。
- 从 replay 主流程中拆出：
  - `ReplayEvaluator`
  - `ReplayReporter`
- `ReplayRunSummary` 固定写入版本矩阵：
  - `analysis_version`
  - `ranking_version`
  - `risk_policy_version`
  - `strategy_runtime_version`
- Replay 汇总固定输出：
  - `decision_breakdown`
  - `selected_strategy_breakdown`
  - `strategy_switch_count`
  - `strategy_switch_attempt_count`
  - `cooldown_block_count`
  - `execution_success_ratio`
  - `final_equity`
  - `final_cash_balance`
  - `final_realized_pnl`
  - `final_unrealized_pnl`
  - `total_fee_paid`
  - `avg_slippage_bps`

### 第 2 周：Strategy Runtime 真正模块化
- 把 `strategy_runtime` 从大分支 service 重构为 `base + registry + strategies/` 插件结构。
- `StrategyRuntimeService` 只负责：
  - 按 `strategy_id` 路由 runtime
  - 执行统一接口
  - 落库 `StrategySignal`
- 第二阶段已有策略改成独立 runtime：
  - `mr_btc_5m_v1`
  - `trend_long_btc_5m_v1`
  - `defensive_no_trade_btc_5m_v1`
- `StrategySignal.action` 正式固定为：
  - `entry`
  - `reduce`
  - `exit`
  - `hold`
  - `no_trade`
- `order_planner` 收口成纯翻译层，只消费：
  - `AuditDecisionOutput`
  - `StrategySignal`
  - 最新盘口/价格上下文

### 第 3 周前半：先落工具执行轨道
- 先于岗位自主化，完成三层工具执行结构：
  - `tool_registry`
  - `schema_guard`
  - `tool_executor`
- 固定执行顺序：
  - 角色校验
  - 输入 schema 校验
  - 工具执行
  - 输出 schema 校验
  - 事件日志落库
- 工具失败统一落 `task_event_log`，至少包含：
  - `tool_acl_denied`
  - `tool_input_invalid`
  - `tool_output_invalid`
  - `tool_runtime_failed`
- 所有内部 router 只能通过工具执行层或 orchestrator facade 调用，不允许 agent 直接自由打底层 service。
- 高风险接口规则固定：
  - 默认仅本机/内网访问
  - `live execution` 端点存在也默认禁用
  - 不允许直接切 `kill switch`

### 第 3 周后半到第 4 周：激活主链岗位自主能力
- 保留 `*_agent.py`，但把它们升级为岗位适配层，不再只是薄包装。
- `AnalystAgent`
  - 先读主分析上下文
  - 证据不足时，通过 `tool_executor` 补取 `orderbook / funding / OI`
  - 输出仍保持单一 `AnalysisAgentOutput`
- `SelectorAgent`
  - 固定产出 `primary / fallback / challenger / no_trade_candidate`
  - 所有排序结果携带 `ranking_version`
- `AuditorAgent`
  - `decision` 仍只允许：
    - `approve`
    - `downgrade`
    - `observe_only`
    - `reject`
  - 不把 `request_more_context` 作为交易决策枚举
  - 新增：
    - `next_action = none | request_more_context`
    - `context_requirements`
  - replay、统计、dashboard 只把 `decision` 计入交易决策分布，`next_action` 单独统计为工作流控制事件
- `MonitorAgent`
  - 增加主动建议能力：
    - `suggest_replay`
    - `suggest_policy_compare`
    - `suggest_strategy_pause`
  - `MonitorSnapshot` 的 source freshness 固定至少区分：
    - `ohlcv`
    - `orderbook`
    - `derivatives_metrics`
    - `strategy_signal`
  - 每个 source 固定输出：
    - `age_seconds`
    - `expected_max_age_seconds`
    - `is_stale`

### 第 5 周：三类旁路探索 Agent 落地，但保持只读/报告型
- 三类旁路 agent 全部实现，但全部不进入主交易链：
  - `replay_planner_agent`
  - `anomaly_reviewer_agent`
  - `tool_gap_agent`
- 职责固定：
  - `replay_planner_agent`
    - 选择回放样本
    - 发起版本矩阵对比
    - 推荐 `risk_policy / strategy_runtime / analysis / ranking` 对照实验
  - `anomaly_reviewer_agent`
    - 回看异常 task 的最近 N 个 cycle
    - 输出归因：`analysis / selection / audit / execution / monitor`
  - `tool_gap_agent`
    - 只做缺口汇总、问题归类、建议报告
    - 不自动生成变更，不自动改配置，不自动改工具注册
- `tool_gap_agent` 在第三阶段固定是观察者和报告者，不拥有任何系统结构修改权。

### 第 6 周：OpenClaw 受控接入，先 5+1 再扩展
- 第三阶段先接入 6 个 OpenClaw workspace：
  - 主链 5 个：`analyst / selector / auditor / executor / monitor`
  - 旁路 1 个：`replay_planner`
- `anomaly_reviewer` 和 `tool_gap` 后端实现会在本阶段完成，但 OpenClaw workspace 暂不首批开放；只有当日志质量、tool executor 稳定性、replay reporter 可用性达标后再补接。
- 每个 OpenClaw agent 固定具备：
  - 独立 workspace
  - 独立 `SOUL.md`
  - 独立 skills
  - 独立 tool whitelist
  - 独立 sandbox 约束
- OpenClaw 只调用岗位 agent adapter 或 `tool_executor`，不直接拼装交易逻辑，不直接调裸 service。
- 第三阶段交付终点固定为：
  - 小额人工监督试运行准备完成
  - `paper/live` 严格分离
  - `live execution` 默认仍关闭

## 接口与类型变化
- `AuditDecisionOutput`
  - `decision: approve | downgrade | observe_only | reject`
  - `next_action: none | request_more_context`
  - `context_requirements: list[str]`
- `StrategySignal`
  - `action: entry | reduce | exit | hold | no_trade`
  - 继续携带 `strategy_runtime_version`
- `ReplayRunSummary`
  - 新增 `version_matrix`
  - 新增 `cooldown_block_count`
- `MonitorSnapshot`
  - 新增 `source_freshness`
  - 至少覆盖 `ohlcv / orderbook / derivatives_metrics / strategy_signal`
- 工具层接口固定为：
  - `tool_registry`
  - `schema_guard`
  - `tool_executor`
- OpenClaw 首批工具集合固定为：
  - `get_market_context`
  - `get_latest_analysis`
  - `get_strategy_candidates`
  - `get_strategy_signal`
  - `preview_audit_decision`
  - `run_paper_cycle`
  - `get_monitor_status`
  - `run_replay_scenario`

## 测试与验收
- 仓库一致性：
  - 根目录无 `.db`
  - `.runtime/` 是唯一运行时输出目录
  - README、runbook、脚本行为一致
- Replay：
  - evaluator/reporter 独立测试
  - 回放 summary 固定带完整版本矩阵
  - `cooldown_block_count` 与切换统计可稳定回归
- Strategy runtime：
  - registry 路由测试
  - 每个 runtime 独立测试
  - planner 不再依赖 `analysis.bias`
  - `entry / reduce / exit / hold / no_trade` 五条路径都有测试
- 工具执行层：
  - ACL 拒绝测试
  - 输入/输出 schema guard 测试
  - 工具失败事件落库测试
- 主链岗位：
  - analyst 补证据路径测试
  - selector 产生 `fallback/challenger/no_trade_candidate` 测试
  - auditor 的 `observe_only + next_action=request_more_context` 路径测试
  - monitor 的 `strategy_signal` freshness 与建议输出测试
- 旁路 agent：
  - replay_planner 能发起版本对比建议
  - anomaly_reviewer 能输出异常归因
  - tool_gap 只能产出报告，不能产生自动变更
- OpenClaw：
  - 首批 6 个 workspace 可启动
  - tool whitelist 生效
  - 主链顺序不可绕过
  - `live execution` 默认返回禁用

## 假设与默认值
- 第三阶段仍保持单仓模块化，不拆多服务部署。
- 主市场继续按 `Binance Futures + paper` 设计，`spot` 继续只保留接口预埋。
- 第三阶段完成三类旁路 agent 的后端实现，但 OpenClaw 首批只开放 `replay_planner`。
- `request_more_context` 固定视为工作流控制动作，不计入交易决策枚举。
- 本阶段不做 live go-live，只做到“小额人工监督试运行准备完成”。
