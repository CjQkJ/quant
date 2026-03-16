"""在 Windows 侧启动可被 WSL OpenClaw 访问的 quant-system API。"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


def detect_wsl_ip(distribution: str) -> str | None:
    """读取指定 WSL 发行版当前的 IPv4 地址。"""

    command = [
        "wsl",
        "-d",
        distribution,
        "--",
        "bash",
        "-lc",
        "hostname -I | awk '{print $1}'",
    ]
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return None
    ip = result.stdout.strip().split()
    return ip[0] if ip else None


def detect_listen_pid(port: str) -> int | None:
    """读取当前占用端口的本地进程 ID。"""

    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        (
            f"Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue | "
            "Select-Object -First 1 -ExpandProperty OwningProcess"
        ),
    ]
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return int(value) if value.isdigit() else None


def probe_health(port: str) -> bool:
    """探测本机 quant-system API 是否已经健康可用。"""

    url = f"http://127.0.0.1:{port}/health"
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return response.status == 200 and b'"status":"ok"' in response.read()
    except (urllib.error.URLError, TimeoutError):
        return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="启动供 WSL OpenClaw 使用的 quant-system API")
    parser.add_argument("--distribution", default="Ubuntu-24.04", help="WSL 发行版名称")
    parser.add_argument("--host", default="0.0.0.0", help="API 监听地址")
    parser.add_argument("--port", default="8000", help="API 监听端口")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    wsl_ip = detect_wsl_ip(args.distribution)
    allowed_hosts = ["127.0.0.1", "localhost", "testclient"]
    if wsl_ip:
        allowed_hosts.append(wsl_ip)

    env = os.environ.copy()
    env["INTERNAL_API_ALLOWED_HOSTS"] = ",".join(allowed_hosts)

    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "apps.agent_orchestrator.main:app",
        "--host",
        args.host,
        "--port",
        args.port,
    ]
    print(f"WSL_IP={wsl_ip or 'unknown'}")
    print(f"INTERNAL_API_ALLOWED_HOSTS={env['INTERNAL_API_ALLOWED_HOSTS']}")
    print("启动命令:", " ".join(command))

    if probe_health(args.port):
        pid = detect_listen_pid(args.port)
        print(f"检测到端口 {args.port} 上已有健康的 quant-system API，直接复用。PID={pid or 'unknown'}")
        return

    existing_pid = detect_listen_pid(args.port)
    if existing_pid:
        raise SystemExit(
            f"端口 {args.port} 已被进程 {existing_pid} 占用，但健康检查未通过。"
            "请先停止该进程，或改用其他端口。"
        )

    subprocess.run(command, cwd=repo_root, env=env, check=True)


if __name__ == "__main__":
    main()
