# OpenClaw Workspace 模板

这里放的是第三阶段首批 `5+1` OpenClaw workspace 模板，不直接承载交易逻辑，只定义：

- 岗位边界
- 工具白名单
- sandbox 约束
- 默认工作方式

首批启用：

- `analyst`
- `selector`
- `auditor`
- `executor`
- `monitor`
- `replay_planner`

后续再开放：

- `anomaly_reviewer`
- `tool_gap`

约束：

- 所有交易相关调用必须经过本地 `tool_executor` 或岗位 adapter
- 不允许直接访问 live execution
- 不允许直接修改 `kill switch`
- `executor` 也只允许触发受控 `paper cycle`

## 部署到本地 OpenClaw

如果你的 OpenClaw 跑在 WSL，推荐直接在 WSL 里执行仓库脚本：

```bash
python3 /mnt/e/quant/quant-system/scripts/deploy_openclaw_workspaces.py \
  --openclaw-root /mnt/e/OpenClaw
```

默认会把首批 `5+1` workspace 部署到：

```text
/mnt/e/OpenClaw/workspace/agents/
```

并自动完成两件事：

- 生成完整 workspace 文件：`SOUL.md / IDENTITY.md / USER.md / TOOLS.md / AGENTS.md / BOOTSTRAP.md / workspace.json`
- 生成 bridge 与本地 skill：`bridge/quant_tool_bridge.py` 和 `skills/quant-bridge/SKILL.md`
- 根据当前 WSL 默认网关写入 `bridge/bridge_config.json`，让 workspace 默认能找到 Windows 侧 API
- 调用 `openclaw agents add` 正式注册 `analyst / selector / auditor / executor / monitor / replay_planner`
- 把 OpenClaw agent 工具权限收口到最小集合：默认只保留 `exec + session_status` 这条桥接通道

部署后可用下面的命令核对：

```bash
openclaw agents list --json
openclaw config validate
python3 /mnt/e/OpenClaw/workspace/agents/analyst/bridge/quant_tool_bridge.py --catalog
```

## 使用约定

OpenClaw agent 不直接读写 `quant-system` 底层服务，而是通过本地 bridge 调用内部 API：

```bash
python3 bridge/quant_tool_bridge.py --tool get_market_context --payload '{"symbol":"BTCUSDT","timeframe":"5m"}'
```

前提是 `quant-system` API 已启动，例如：

```bash
cd /mnt/e/quant/quant-system
python -m uvicorn apps.agent_orchestrator.main:app --host 127.0.0.1 --port 8000
```

如果 API 跑在 Windows、OpenClaw 跑在 WSL，推荐直接用仓库脚本启动，它会自动把当前 WSL IP 加入内部 API 白名单：

```bash
cd E:\quant\quant-system
python scripts/start_api_for_openclaw.py --distribution Ubuntu-24.04
```

注意：这条命令只是“启动或复用 Windows 侧的 quant-system API”，不会进入 WSL，也不会自动打开 `openclaw tui`。它的作用相当于先把后端服务准备好，供 WSL 里的 OpenClaw workspace 通过 bridge 调用。

## 最短使用教程

### 1. 在 Windows 里启动或复用 quant-system API

```powershell
cd E:\quant\quant-system
python scripts\start_api_for_openclaw.py --distribution Ubuntu-24.04
```

看到下面这类输出就说明后端已经可用了：

```text
检测到端口 8000 上已有健康的 quant-system API，直接复用。
```

或者：

```text
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. 在 WSL 里部署或刷新 OpenClaw workspaces

```bash
wsl -d Ubuntu-24.04
cd /mnt/e/quant/quant-system
python3 scripts/deploy_openclaw_workspaces.py --openclaw-root /mnt/e/OpenClaw
```

这一步会：

- 刷新 `E:\OpenClaw\workspace\agents\...` 下的 6 个 workspace
- 注册或更新 `analyst / selector / auditor / executor / monitor / replay_planner`
- 刷新 bridge 和本地 skill

### 3. 在 WSL 里直接验证 bridge

先看 `analyst` 允许的 quant-system 工具：

```bash
python3 /mnt/e/OpenClaw/workspace/agents/analyst/bridge/quant_tool_bridge.py --catalog
```

再看 `executor`：

```bash
python3 /mnt/e/OpenClaw/workspace/agents/executor/bridge/quant_tool_bridge.py --catalog
```

### 4. 在 WSL 里定向调用某个 OpenClaw agent

```bash
openclaw agent --agent analyst --message "你有哪些工具"
openclaw agent --agent executor --message "你有哪些工具"
```

### 5. 如果你想打开 TUI

```bash
openclaw tui
```

但要注意：`tui` 默认连的是 `main` 会话，不会自动切到 `analyst / selector / auditor ...`。当前最稳的方式仍然是：

```bash
openclaw agent --agent <agent_id> --message "..."
```

## 常见误区

- `python scripts/start_api_for_openclaw.py ...`
  只是启动或复用 API，不会进入 WSL
- `openclaw tui`
  只是打开 OpenClaw 的终端 UI，不会自动替你选择新的岗位 agent
- 真正的调用链是：
  Windows API -> WSL OpenClaw agent -> workspace bridge -> quant-system `/tools/*`

当前默认只接入首批 `5+1`。`anomaly_reviewer` 和 `tool_gap` 仍保持后端已实现、OpenClaw workspace 暂缓开放的策略。
