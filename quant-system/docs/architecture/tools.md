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
- 高风险工具只允许内部调用
- `run_paper_execution` 作为兼容旧名称保留，但以 `run_paper_cycle` 为主

禁止项：

- 真实下单
- 直接修改策略代码
- 直接修改 `kill switch`
- 绕过 `audit -> execution` 链路
