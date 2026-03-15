"""写入默认策略元数据。"""

from apps.strategy_registry.services.registry_service import RegistryService
from shared.db.session import session_scope


if __name__ == "__main__":
    service = RegistryService()
    with session_scope() as session:
        service.seed_default_strategies(session)
        session.commit()
    print("默认策略写入完成")

