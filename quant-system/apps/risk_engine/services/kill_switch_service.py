"""Kill switch 服务。"""

from __future__ import annotations

from shared.utils.state_store import StateStore


class KillSwitchService:
    KEY = "runtime:kill_switch"

    def __init__(self, state_store: StateStore) -> None:
        self.state_store = state_store

    def is_enabled(self) -> bool:
        return self.state_store.get_bool(self.KEY, default=False)

    def set_enabled(self, enabled: bool) -> None:
        self.state_store.set_bool(self.KEY, enabled)

