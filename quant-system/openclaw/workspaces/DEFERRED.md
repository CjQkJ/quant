# Deferred Workspaces

这两个旁路 agent 的后端实现已在第三阶段落地，但不作为首批 OpenClaw workspace 开放：

- `anomaly_reviewer`
- `tool_gap`

原因：

- 它们更依赖完整事件日志质量
- 也更依赖 replay report 和 tool executor 的成熟度
