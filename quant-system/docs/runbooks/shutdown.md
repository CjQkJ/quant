# 停机 Runbook

1. 如正在跑回放或演示，先等待当前 cycle 完成。
2. 如需阻止新的 paper execution，先调用内部 API 打开 `kill switch`：
   `POST /risk/kill-switch/true`
3. 停止 API：
   `Ctrl+C` 或停止对应进程。
4. 如使用 Docker 基础设施：
   `docker compose stop postgres redis`
5. 如需清理本地演示状态，只清理 `.runtime/`，不要动 `tests/fixtures/`。

补充说明：

- `kill switch` 开启后，新的执行请求会被拦截。
- `live execution` 默认关闭，不存在停机前“撤 live 权限”的额外步骤。
