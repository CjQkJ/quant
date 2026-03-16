from apps.strategy_registry.schemas.strategy import RankedCandidate
from apps.strategy_registry.services.selection_policy_service import SelectionPolicyService
from shared.utils.state_store import InMemoryStateStore


def test_selection_policy_blocks_switch_within_cooldown():
    service = SelectionPolicyService(InMemoryStateStore())
    first_ranked = [
        RankedCandidate(strategy_id="mr_btc_5m_v1", strategy_name="MR", fit_score=0.9, reason="a", strategy_type="mean_reversion"),
        RankedCandidate(strategy_id="trend_long_btc_5m_v1", strategy_name="Trend", fit_score=0.8, reason="b", strategy_type="trend_following"),
    ]
    second_ranked = [
        RankedCandidate(strategy_id="trend_long_btc_5m_v1", strategy_name="Trend", fit_score=0.95, reason="c", strategy_type="trend_following"),
        RankedCandidate(strategy_id="mr_btc_5m_v1", strategy_name="MR", fit_score=0.7, reason="d", strategy_type="mean_reversion"),
    ]

    primary, switch_attempted, cooldown_applied, note = service.apply(symbol="BTCUSDT", timeframe="5m", ranked=first_ranked)
    assert primary.strategy_id == "mr_btc_5m_v1"
    assert switch_attempted is False
    assert cooldown_applied is False
    assert note == "normal"

    primary, switch_attempted, cooldown_applied, note = service.apply(symbol="BTCUSDT", timeframe="5m", ranked=second_ranked)
    assert primary.strategy_id == "mr_btc_5m_v1"
    assert switch_attempted is True
    assert cooldown_applied is True
    assert note == "cooldown_locked_previous_strategy"
