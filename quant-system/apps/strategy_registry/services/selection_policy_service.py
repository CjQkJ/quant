"""策略选择冷却策略。"""

from __future__ import annotations

from datetime import datetime

from apps.strategy_registry.schemas.strategy import RankedCandidate
from shared.config.risk_policy import get_risk_policy
from shared.utils.state_store import StateStore
from shared.utils.time import ensure_utc, utc_now


class SelectionPolicyService:
    """负责处理策略切换冷却。"""

    def __init__(self, state_store: StateStore) -> None:
        self.state_store = state_store

    def apply(
        self,
        *,
        symbol: str,
        timeframe: str,
        ranked: list[RankedCandidate],
    ) -> tuple[RankedCandidate, bool, bool, str]:
        if not ranked:
            raise ValueError("候选策略为空，无法应用选择策略")

        policy = get_risk_policy()
        primary = ranked[0]
        state_key = f"selection:last:{symbol}:{timeframe}"
        previous = self.state_store.get_json(state_key, {})
        previous_strategy_id = previous.get("strategy_id")
        previous_at_raw = previous.get("selected_at")

        switch_attempted = bool(previous_strategy_id and previous_strategy_id != primary.strategy_id)
        cooldown_applied = False
        note = "normal"

        if switch_attempted and previous_at_raw:
            previous_at = ensure_utc(datetime.fromisoformat(previous_at_raw))
            cooldown_seconds = (utc_now() - previous_at).total_seconds()
            if cooldown_seconds < policy.strategy_switch_cooldown_seconds:
                previous_candidate = next((item for item in ranked if item.strategy_id == previous_strategy_id), None)
                if previous_candidate is not None:
                    primary = previous_candidate
                    cooldown_applied = True
                    note = "cooldown_locked_previous_strategy"

        if not cooldown_applied:
            self.state_store.set_json(
                state_key,
                {
                    "strategy_id": primary.strategy_id,
                    "selected_at": utc_now().isoformat(),
                },
            )

        return primary, switch_attempted, cooldown_applied, note
