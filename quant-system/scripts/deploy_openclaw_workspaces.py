"""将 quant-system 的 OpenClaw workspace 模板部署到本地 OpenClaw 环境。"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_AGENTS = [
    "analyst",
    "selector",
    "auditor",
    "executor",
    "monitor",
    "replay_planner",
]

OPENCLAW_CORE_ALLOW = ["exec", "session_status"]
OPENCLAW_CORE_DENY = [
    "read",
    "edit",
    "write",
    "apply_patch",
    "image",
    "browser",
    "canvas",
    "process",
    "sessions_list",
    "sessions_history",
    "sessions_send",
    "sessions_spawn",
    "sessions_yield",
    "subagents",
    "web_search",
    "web_fetch",
    "nodes",
    "cron",
    "gateway",
]


@dataclass(frozen=True)
class AgentIdentity:
    """OpenClaw agent 的身份信息。"""

    display_name: str
    emoji: str
    theme: str
    creature: str
    vibe: str


IDENTITY_MAP: dict[str, AgentIdentity] = {
    "analyst": AgentIdentity("量化分析岗", "📊", "slate", "受控观察者", "冷静、证据优先、只给结构化判断"),
    "selector": AgentIdentity("策略选择岗", "🧭", "indigo", "排序协调者", "保守、重比较、只从预置策略里挑选"),
    "auditor": AgentIdentity("风控审核岗", "🛡️", "amber", "风险守门员", "严格、可解释、优先保护系统"),
    "executor": AgentIdentity("模拟执行岗", "⚙️", "emerald", "纸面交易执行器", "克制、机械、绝不越权"),
    "monitor": AgentIdentity("系统监控岗", "🛰️", "cyan", "状态巡检员", "持续观察、主动预警、只提建议"),
    "replay_planner": AgentIdentity("回放规划岗", "🧪", "rose", "实验规划者", "对照驱动、偏研究、只做 replay 建议"),
}


def run_command(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """执行命令并返回完整结果。"""

    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def load_workspace_meta(template_dir: Path) -> dict[str, Any]:
    """读取 workspace 模板元信息。"""

    return json.loads((template_dir / "workspace.json").read_text(encoding="utf-8"))


def render_identity(agent_id: str) -> str:
    """生成 IDENTITY.md。"""

    identity = IDENTITY_MAP[agent_id]
    return f"""# IDENTITY.md - Who Am I?

- **Name:** {identity.display_name}
- **Creature:** {identity.creature}
- **Vibe:** {identity.vibe}
- **Emoji:** {identity.emoji}
- **Theme:** {identity.theme}
- **Avatar:**

---

本工作区用于 `quant-system` 第三阶段 OpenClaw 接入。
只允许在岗位边界内使用受控工具，不直接承载交易逻辑。
"""


def render_user(openclaw_root: Path) -> str:
    """生成 USER.md。"""

    return f"""# USER.md - About Your Human

- **Name:** CQJ
- **What to call them:** 用户
- **Timezone:** Asia/Shanghai
- **Notes:** 主要项目是 `quant-system`，沟通和文档以中文为主。

## Context

- 当前关注的是多智能体量化交易系统的受控演进，而不是直接追求实盘自动化。
- OpenClaw 安装根目录：`{openclaw_root}`
- 代码仓库根目录：`/mnt/e/quant/quant-system`
- 关键原则：不绕过风控链路，不编造字段，不在证据不足时强行下结论。
"""


def render_tools(meta: dict[str, Any]) -> str:
    """生成 TOOLS.md。"""

    whitelist = "\n".join(f"- `{tool}`" for tool in meta.get("tool_whitelist", []))
    skills = "\n".join(f"- `{skill}`" for skill in meta.get("skills", []))
    return f"""# TOOLS.md - Local Notes

## 受控工具白名单

{whitelist or "- 无"}

## 对应 skills

{skills or "- 无"}

## 约束

- 所有工具调用都必须经过 `tool_executor`
- 调用 quant-system 内部 API 时，统一走 `bridge/quant_tool_bridge.py`
- 高风险接口默认只允许 paper / replay
- 不直接触发 `live execution`
- 不直接修改 `kill switch`

## 桥接命令

先查看当前岗位允许的工具目录：

```bash
python3 bridge/quant_tool_bridge.py --catalog
```

执行具体工具：

```bash
python3 bridge/quant_tool_bridge.py --tool <tool_name> --payload '{{"symbol":"BTCUSDT","timeframe":"5m"}}'
```
"""


def render_agents(agent_id: str, meta: dict[str, Any]) -> str:
    """生成 AGENTS.md。"""

    return f"""# AGENTS.md

本工作区属于 `quant-system` 的 `{agent_id}` 岗位。

## 固定要求

- 只在当前岗位职责内行动
- 输出必须满足对应 schema；如果证据不足，明确暴露缺口
- 默认 sandbox：`{meta.get("sandbox", "unknown")}`
- 不直接访问 live execution、kill switch、底层裸 service
- 所有内部能力访问都通过受控工具或岗位 facade
"""


def render_bootstrap(agent_id: str) -> str:
    """生成 BOOTSTRAP.md。"""

    return f"""# BOOTSTRAP.md

进入 `{agent_id}` 工作区后，固定按下面顺序读取上下文：

1. `SOUL.md`
2. `IDENTITY.md`
3. `USER.md`
4. `TOOLS.md`
5. `AGENTS.md`
6. `workspace.json`

如果当前任务超出岗位边界，返回边界说明，不自行扩权。
"""


def render_skill(agent_id: str, meta: dict[str, Any]) -> str:
    """生成 quant-bridge skill。"""

    whitelist = "\n".join(f"- `{tool}`" for tool in meta.get("tool_whitelist", []))
    return f"""# quant-bridge

当前工作区对应的岗位是 `{agent_id}`。

## 何时使用

- 需要读取 quant-system 的最新上下文
- 需要调用受控 `tool_executor` 工具
- 需要确认自己当前岗位允许哪些工具

## 固定做法

1. 先查看工具目录：

```bash
python3 bridge/quant_tool_bridge.py --catalog
```

2. 再执行具体工具：

```bash
python3 bridge/quant_tool_bridge.py --tool <tool_name> --payload '{{"symbol":"BTCUSDT","timeframe":"5m"}}'
```

## 当前岗位允许工具

{whitelist or "- 无"}

## 约束

- 只调用 `workspace.json` 里的白名单工具
- 如果桥接不可用，明确返回 `bridge_unavailable`
- 不使用通用读写工具绕过 bridge
- 不直接访问 live execution 和 kill switch
"""


def detect_wsl_gateway() -> str | None:
    """读取当前 WSL 默认网关。"""

    result = run_command(["bash", "-lc", "ip route show default"])
    if result.returncode != 0:
        return None
    text = result.stdout.strip()
    if " via " not in text:
        return None
    return text.split(" via ", 1)[1].split()[0].strip()


def ensure_bridge(repo_root: Path, workspace_dir: Path, agent_id: str, meta: dict[str, Any]) -> None:
    """生成 workspace bridge 脚本与 skill。"""

    template = repo_root / "openclaw" / "templates" / "quant_tool_bridge.py"
    bridge_dir = workspace_dir / "bridge"
    skill_dir = workspace_dir / "skills" / "quant-bridge"
    bridge_dir.mkdir(parents=True, exist_ok=True)
    skill_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template, bridge_dir / "quant_tool_bridge.py")
    gateway = detect_wsl_gateway()
    bridge_config = {"default_base_url": f"http://{gateway}:8000"} if gateway else {}
    (bridge_dir / "bridge_config.json").write_text(
        json.dumps(bridge_config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (skill_dir / "SKILL.md").write_text(render_skill(agent_id, meta), encoding="utf-8")


def ensure_workspace(repo_root: Path, template_dir: Path, workspace_dir: Path, openclaw_root: Path) -> dict[str, Any]:
    """根据模板生成完整 workspace。"""

    agent_id = template_dir.name
    meta = load_workspace_meta(template_dir)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template_dir / "SOUL.md", workspace_dir / "SOUL.md")
    shutil.copy2(template_dir / "workspace.json", workspace_dir / "workspace.json")
    (workspace_dir / "IDENTITY.md").write_text(render_identity(agent_id), encoding="utf-8")
    (workspace_dir / "USER.md").write_text(render_user(openclaw_root), encoding="utf-8")
    (workspace_dir / "TOOLS.md").write_text(render_tools(meta), encoding="utf-8")
    (workspace_dir / "AGENTS.md").write_text(render_agents(agent_id, meta), encoding="utf-8")
    (workspace_dir / "BOOTSTRAP.md").write_text(render_bootstrap(agent_id), encoding="utf-8")
    ensure_bridge(repo_root, workspace_dir, agent_id, meta)
    return meta


def list_existing_agents() -> dict[str, dict[str, Any]]:
    """读取当前 OpenClaw agent 列表。"""

    result = run_command(["openclaw", "agents", "list", "--json"])
    if result.returncode == 0:
        return {item["id"]: item for item in json.loads(result.stdout)}

    config_path = get_config_path()
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    return {
        item["id"]: item
        for item in payload.get("agents", {}).get("list", [])
        if isinstance(item, dict) and item.get("id")
    }


def get_config_path() -> Path:
    """返回 OpenClaw 配置文件路径。"""

    result = run_command(["openclaw", "config", "file"])
    if result.returncode != 0:
        fallback = Path.home() / ".openclaw" / "openclaw.json"
        if fallback.exists():
            return fallback.resolve()
        raise RuntimeError(f"读取 OpenClaw 配置路径失败：{result.stderr.strip() or result.stdout.strip()}")
    return Path(result.stdout.strip().replace("~", str(Path.home()))).expanduser().resolve()


def ensure_agent_registered(agent_id: str, workspace_dir: Path) -> str:
    """确保 agent 已注册到 OpenClaw。"""

    existing = list_existing_agents()
    if agent_id not in existing:
        result = run_command(
            [
                "openclaw",
                "agents",
                "add",
                agent_id,
                "--workspace",
                str(workspace_dir),
                "--non-interactive",
                "--json",
            ]
        )
        if result.returncode != 0:
            raise RuntimeError(f"注册 agent `{agent_id}` 失败：{result.stderr.strip() or result.stdout.strip()}")
        return "created"

    configured_workspace = Path(existing[agent_id]["workspace"]).resolve()
    if configured_workspace != workspace_dir.resolve():
        raise RuntimeError(
            f"agent `{agent_id}` 已存在，但 workspace 不一致："
            f"{configured_workspace} != {workspace_dir.resolve()}"
        )
    return "existing"


def sync_agent_config(config_path: Path, agent_ids: list[str]) -> None:
    """直接修正 openclaw.json 中的身份和工具权限。"""

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    for item in payload.get("agents", {}).get("list", []):
        agent_id = item.get("id")
        if agent_id not in agent_ids or agent_id not in IDENTITY_MAP:
            continue
        identity = IDENTITY_MAP[agent_id]
        item.setdefault("identity", {})
        item["identity"]["name"] = identity.display_name
        item["identity"]["theme"] = identity.theme
        item["identity"]["emoji"] = identity.emoji
        item["tools"] = {
            "profile": "coding",
            "allow": OPENCLAW_CORE_ALLOW,
            "deny": OPENCLAW_CORE_DENY,
            "sandbox": {
                "tools": {
                    "allow": OPENCLAW_CORE_ALLOW,
                    "deny": OPENCLAW_CORE_DENY,
                }
            },
        }

    config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(description="部署 quant-system 的 OpenClaw workspaces")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="quant-system 仓库根目录",
    )
    parser.add_argument(
        "--openclaw-root",
        type=Path,
        default=Path("/mnt/e/OpenClaw"),
        help="OpenClaw 安装根目录",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="OpenClaw agent workspace 根目录，默认是 <openclaw-root>/workspace/agents",
    )
    parser.add_argument(
        "--agents",
        nargs="*",
        default=DEFAULT_AGENTS,
        help="要部署的 agent 列表，默认部署首批 5+1",
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON 摘要")
    return parser.parse_args()


def main() -> None:
    """主入口。"""

    args = parse_args()
    repo_root = args.repo_root.resolve()
    openclaw_root = args.openclaw_root.resolve()
    workspace_root = (args.workspace_root or (openclaw_root / "workspace" / "agents")).resolve()
    template_root = repo_root / "openclaw" / "workspaces"

    if shutil.which("openclaw") is None:
        raise SystemExit("未找到 `openclaw` 命令，请在已安装 OpenClaw CLI 的环境中执行。")
    if not template_root.exists():
        raise SystemExit(f"未找到模板目录：{template_root}")

    config_path = get_config_path()
    summary: list[dict[str, Any]] = []
    for agent_id in args.agents:
        template_dir = template_root / agent_id
        if not template_dir.exists():
            raise SystemExit(f"未找到 agent 模板：{template_dir}")

        workspace_dir = workspace_root / agent_id
        meta = ensure_workspace(repo_root, template_dir, workspace_dir, openclaw_root)
        status = ensure_agent_registered(agent_id, workspace_dir)
        summary.append(
            {
                "agent_id": agent_id,
                "status": status,
                "workspace": str(workspace_dir),
                "sandbox": meta.get("sandbox"),
                "tool_whitelist": meta.get("tool_whitelist", []),
            }
        )

    sync_agent_config(config_path, list(args.agents))
    validate = run_command(["openclaw", "config", "validate"])
    if validate.returncode != 0:
        raise RuntimeError(f"OpenClaw 配置校验失败：{validate.stderr.strip() or validate.stdout.strip()}")

    if args.json:
        json.dump({"workspace_root": str(workspace_root), "agents": summary}, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return

    print(f"已部署 OpenClaw workspace 根目录：{workspace_root}")
    for item in summary:
        tools = ", ".join(item["tool_whitelist"])
        print(f"- {item['agent_id']}: {item['status']} -> {item['workspace']} | tools={tools}")
    print("OpenClaw 配置校验通过。")


if __name__ == "__main__":
    main()
