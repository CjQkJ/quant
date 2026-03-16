"""OpenClaw workspace 到 quant-system 内部工具 API 的桥接脚本。"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_workspace_meta() -> dict[str, Any]:
    return json.loads((workspace_root() / "workspace.json").read_text(encoding="utf-8"))


def load_bridge_config() -> dict[str, Any]:
    path = workspace_root() / "bridge" / "bridge_config.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_role_id(raw_role: str) -> str:
    if raw_role.endswith("_agent"):
        return raw_role
    return f"{raw_role}_agent"


def resolve_base_urls(explicit_base_url: str | None) -> list[str]:
    candidates: list[str] = []
    if explicit_base_url:
        candidates.append(explicit_base_url.rstrip("/"))
    env_url = os.getenv("QUANT_SYSTEM_API", "").strip()
    if env_url:
        candidates.append(env_url.rstrip("/"))
    config_url = str(load_bridge_config().get("default_base_url", "")).strip()
    if config_url:
        candidates.append(config_url.rstrip("/"))
    candidates.append("http://127.0.0.1:8000")

    route_output = os.popen("ip route show default 2>/dev/null").read().strip()
    if " via " in route_output:
        host_ip = route_output.split(" via ", 1)[1].split()[0].strip()
        if host_ip:
            candidates.append(f"http://{host_ip}:8000")
    candidates.append("http://host.docker.internal:8000")

    deduped: list[str] = []
    for item in candidates:
        if item and item not in deduped:
            deduped.append(item)
    return deduped


def call_json(method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url=url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="quant-system OpenClaw 桥接工具")
    parser.add_argument("--role", default=None, help="岗位 id，默认读取 workspace.json")
    parser.add_argument("--base-url", default=None, help="显式指定 quant-system API 地址")
    parser.add_argument("--catalog", action="store_true", help="读取当前岗位允许的工具目录")
    parser.add_argument("--tool", default=None, help="要执行的工具名")
    parser.add_argument("--payload", default="{}", help="JSON 字符串形式的 payload")
    parser.add_argument("--task-id", default=None, help="可选 task_id")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    meta = load_workspace_meta()
    role = resolve_role_id(args.role or meta.get("workspace_name") or workspace_root().name)
    allowed_tools = set(meta.get("tool_whitelist", []))
    base_urls = resolve_base_urls(args.base_url)

    try:
        if args.catalog:
            last_error = None
            for base_url in base_urls:
                try:
                    result = call_json("GET", f"{base_url}/tools/catalog/{role}")
                    print(json.dumps({"role": role, "base_url": base_url, "catalog": result}, ensure_ascii=False, indent=2))
                    return
                except urllib.error.URLError as error:
                    last_error = error
            raise urllib.error.URLError(last_error.reason if last_error else "bridge_unavailable")

        if not args.tool:
            raise SystemExit("未提供 `--tool`，请使用 `--catalog` 或指定具体工具名。")
        if args.tool not in allowed_tools:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": "tool_not_allowed",
                        "role": role,
                        "tool": args.tool,
                        "allowed_tools": sorted(allowed_tools),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            raise SystemExit(2)

        payload = json.loads(args.payload)
        last_error = None
        for base_url in base_urls:
            try:
                result = call_json(
                    "POST",
                    f"{base_url}/tools/execute/{role}/{args.tool}",
                    {"task_id": args.task_id, "payload": payload},
                )
                result["base_url"] = base_url
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return
            except urllib.error.URLError as error:
                last_error = error
        raise urllib.error.URLError(last_error.reason if last_error else "bridge_unavailable")
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "http_error",
                    "status": error.code,
                    "body": body,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        raise SystemExit(3)
    except urllib.error.URLError as error:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "bridge_unavailable",
                    "detail": str(error.reason),
                    "base_urls": base_urls,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        raise SystemExit(4)


if __name__ == "__main__":
    main()
