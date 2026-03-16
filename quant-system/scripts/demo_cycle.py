"""一键演示当前多智能体闭环。"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from sqlalchemy import select

from apps.strategy_registry.services.registry_service import RegistryService
from shared.db.session import init_db, session_scope
from shared.models.tables import TaskEventLog
from shared.utils.demo_data import seed_market_data
from shared.utils.state_store import InMemoryStateStore


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数。"""

    parser = argparse.ArgumentParser(description="演示 quant-system 当前可运行效果")
    parser.add_argument("--symbol", default="BTCUSDT", help="演示交易对，默认 BTCUSDT")
    parser.add_argument("--timeframe", default="5m", help="演示周期，默认 5m")
    parser.add_argument(
        "--mode",
        default="trend",
        choices=["trend", "low_confidence", "downtrend"],
        help="演示行情模式：trend 为顺风场景，low_confidence 为观望场景，downtrend 为偏空场景",
    )
    parser.add_argument(
        "--database-url",
        default="sqlite+pysqlite:///./.runtime/demo_cycle.db",
        help="演示用数据库连接，默认写到 .runtime/demo_cycle.db",
    )
    parser.add_argument(
        "--redis-url",
        default="memory://",
        help="演示用状态存储连接，默认使用内存模式",
    )
    parser.add_argument("--kill-switch-on", action="store_true", help="演示风控拦截路径，强制打开 kill switch")
    parser.add_argument("--keep-db", action="store_true", help="保留现有演示数据库，不在启动前删除")
    parser.add_argument("--json", action="store_true", help="输出完整 JSON 结果")
    return parser


def maybe_reset_sqlite_file(database_url: str, keep_db: bool) -> None:
    """为了避免重复插入演示数据，默认重置 sqlite 文件。"""

    if keep_db or not database_url.startswith("sqlite+pysqlite:///"):
        return
    raw_path = database_url.removeprefix("sqlite+pysqlite:///")
    database_path = Path(raw_path)
    if database_path.exists():
        database_path.unlink()


def configure_env(database_url: str, redis_url: str) -> None:
    """设置运行时环境变量。"""

    os.environ["DATABASE_URL"] = database_url
    os.environ["REDIS_URL"] = redis_url


def print_text_summary(
    result,
    event_logs: list[TaskEventLog],
    mode: str,
    database_url: str,
    kill_switch_on: bool,
) -> None:
    """输出适合人工阅读的结果摘要。"""

    print("演示完成")
    print(f"演示模式: {mode}")
    print(f"数据库: {database_url}")
    print(f"强制 Kill Switch: {kill_switch_on}")
    print("")
    print("流程概览")
    for event in event_logs:
        print(f"- {event.event_type} <- {event.event_source}")
    print("")
    print("分析结果")
    print(f"- 市场状态: {result.analysis.market_regime}")
    print(f"- 方向偏向: {result.analysis.directional_bias}")
    print(f"- 置信度: {result.analysis.confidence:.2f}")
    print(f"- 流动性等级: {result.analysis.liquidity_level}")
    print(f"- 分析版本: {result.analysis_version}")
    print("")
    print("策略与审核")
    print(f"- 选中策略: {result.selection.selected_strategy_name}")
    print(f"- 选中原因: {result.selection.selection_reason}")
    print(f"- 排序版本: {result.ranking_version}")
    print(f"- 策略信号: {result.strategy_signal.action} / {result.strategy_signal.direction}")
    print(f"- 策略运行版本: {result.strategy_runtime_version}")
    print(f"- 审核结论: {result.audit.decision}")
    print(f"- 审核摘要: {result.audit.audit_summary}")
    print(f"- 风控版本: {result.risk_policy_version}")
    print("")
    print("执行与监控")
    print(f"- 执行状态: {result.execution.execution_status}")
    print(f"- 执行摘要: {result.execution.execution_summary}")
    print(f"- 账户权益: {result.account_snapshot.equity:.2f}")
    print(f"- 已实现盈亏: {result.account_snapshot.realized_pnl:.2f}")
    print(f"- 未实现盈亏: {result.account_snapshot.unrealized_pnl:.2f}")
    print(f"- 系统状态: {result.monitor.system_status}")
    print(f"- Kill Switch: {result.monitor.kill_switch}")
    print("")
    print("提示")
    print("- 这是 paper trading 演示，不会真实下单")
    print("- 如果要看完整结构化输出，可追加 --json")


def main() -> None:
    """运行演示流程。"""

    parser = build_parser()
    args = parser.parse_args()

    maybe_reset_sqlite_file(args.database_url, args.keep_db)
    configure_env(args.database_url, args.redis_url)
    init_db()

    from apps.agent_orchestrator.main import OrchestratorService

    state_store = InMemoryStateStore()
    if args.kill_switch_on:
        state_store.set_bool("runtime:kill_switch", True)

    with session_scope() as session:
        RegistryService().seed_default_strategies(session)
        seed_market_data(session, mode=args.mode)
        result = OrchestratorService(state_store=state_store).run_cycle(
            session,
            symbol=args.symbol,
            timeframe=args.timeframe,
        )
        event_logs = list(
            session.scalars(
                select(TaskEventLog)
                .where(TaskEventLog.task_id == result.task_id)
                .order_by(TaskEventLog.id.asc())
            ).all()
        )
        session.commit()

    if args.json:
        print(result.model_dump_json(indent=2))
        return

    print_text_summary(result, event_logs, args.mode, args.database_url, args.kill_switch_on)


if __name__ == "__main__":
    main()
