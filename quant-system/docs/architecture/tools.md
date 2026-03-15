# OpenClaw 工具清单

第一阶段只暴露低风险、本地可验证的工具：

- `read_market_data`
- `read_orderbook`
- `read_derivatives_metrics`
- `read_strategy_registry`
- `read_analysis_report`
- `read_strategy_selection`
- `read_risk_state`
- `run_paper_execution`
- `read_system_state`
- `read_execution_orders`
- `raise_alert`

禁止项：

- 真实下单
- 直接修改策略代码
- 直接修改 `kill switch`

