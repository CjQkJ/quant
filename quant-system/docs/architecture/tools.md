# OpenClaw 工具清单

第二阶段冻结的内部工具集合：

- `get_market_context`
- `get_latest_analysis`
- `get_strategy_candidates`
- `get_strategy_signal`
- `preview_audit_decision`
- `run_paper_cycle`
- `get_monitor_status`
- `run_replay_scenario`

约束：

- 所有工具输入输出都过 Pydantic schema
- 所有工具调用统一走 `tool_registry -> schema_guard -> tool_executor`
- 输入无效、输出无效、ACL 拒绝、运行失败都要单独落 `task_event_log`
- 高风险工具只允许内部调用
- `run_paper_execution` 作为兼容旧名称保留，但以 `run_paper_cycle` 为主

新增说明：

- `POST /tools/execute/{role}/{tool_name}` 是内部受控执行入口
- `preview_audit_decision` 现在是只读预览，不会落库
- `GET /replay/plan` 提供 replay_planner 的版本矩阵建议
- `GET /tools/gap-report` 提供 tool_gap 的只读建议报告
- OpenClaw agent 输出如果不符合约定 schema，必须记录 `openclaw_agent_output_invalid`
- `anomaly_reviewer_agent` 当前只允许只读复盘，不允许触发写操作或系统变更

禁止项：

- 真实下单
- 直接修改策略代码
- 直接修改 `kill switch`
- 绕过 `audit -> execution` 链路
