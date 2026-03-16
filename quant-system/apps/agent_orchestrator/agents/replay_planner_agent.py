"""回放规划智能体。"""

from __future__ import annotations

from apps.agent_orchestrator.schemas.replay_plan import ReplayPlannerInput, ReplayPlannerOutput, VersionTarget
from shared.config.risk_policy import get_risk_policy
from shared.constants.versions import ANALYSIS_VERSION, RANKING_VERSION, STRATEGY_RUNTIME_VERSION
from shared.utils.ids import build_id
from shared.utils.time import utc_now


class ReplayPlannerAgent:
    def run(self, request: ReplayPlannerInput) -> ReplayPlannerOutput:
        policy = get_risk_policy()
        baseline = VersionTarget(
            analysis_version=ANALYSIS_VERSION,
            ranking_version=RANKING_VERSION,
            risk_policy_version=policy.version,
            strategy_runtime_version=STRATEGY_RUNTIME_VERSION,
            reason="当前默认基线版本矩阵",
        )
        comparison_targets = [
            VersionTarget(
                analysis_version=baseline.analysis_version,
                ranking_version=baseline.ranking_version,
                risk_policy_version=baseline.risk_policy_version,
                strategy_runtime_version=baseline.strategy_runtime_version,
                reason="先重放当前基线，确保结果稳定后再做版本对照",
            )
        ]
        return ReplayPlannerOutput(
            plan_id=build_id("replay_plan"),
            plan_time=utc_now(),
            symbol=request.symbol,
            timeframe=request.timeframe,
            fixture_name=request.fixture_name,
            baseline=baseline,
            comparison_targets=comparison_targets,
            summary="优先回放当前版本矩阵；如监控建议 policy compare，再替换单一版本号做对照实验",
        )
