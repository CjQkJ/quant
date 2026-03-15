"""运行回放。"""

import os
from pathlib import Path

from apps.agent_orchestrator.replay.replay_loader import ReplayLoader
from apps.agent_orchestrator.replay.replay_runner import ReplayRunner
from apps.strategy_registry.services.registry_service import RegistryService
from shared.db.session import init_db, session_scope
from shared.utils.demo_data import seed_market_data
from shared.utils.state_store import InMemoryStateStore


def configure_demo_env() -> None:
    """为回放脚本准备独立演示环境。"""

    if "DATABASE_URL" not in os.environ:
        demo_db = Path("replay_demo.db")
        if demo_db.exists():
            demo_db.unlink()
        os.environ["DATABASE_URL"] = "sqlite+pysqlite:///./replay_demo.db"
    os.environ.setdefault("REDIS_URL", "memory://")


if __name__ == "__main__":
    configure_demo_env()
    init_db()
    from apps.agent_orchestrator.main import OrchestratorService

    loader = ReplayLoader()
    fixture = Path("tests/fixtures/replay_bars.json")
    bars = loader.load_json(fixture)
    runner = ReplayRunner(OrchestratorService(state_store=InMemoryStateStore()))
    with session_scope() as session:
        RegistryService().seed_default_strategies(session)
        seed_market_data(session, mode="trend")
        session.commit()
        results = runner.run(session, bars=bars, symbol="BTCUSDT", timeframe="5m")
    print(f"回放完成，共 {len(results)} 个 bar")
