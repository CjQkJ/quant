"""只读异常复盘智能体。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.agent_orchestrator.schemas.anomaly_review import AnomalyReviewerInput, AnomalyReviewerOutput, ReviewedEvent
from shared.models.tables import TaskEventLog
from shared.utils.ids import build_id
from shared.utils.time import utc_now


class AnomalyReviewerAgent:
    """异常复盘只允许读取事件和结果，不允许修改系统状态。"""

    READ_ONLY_MODELS = ("task_event_log", "analysis_report", "strategy_selection", "audit_decision", "execution_order", "monitor_snapshot")

    def run(self, session: Session, request: AnomalyReviewerInput) -> AnomalyReviewerOutput:
        events = list(
            reversed(
                session.scalars(
                    select(TaskEventLog)
                    .where(TaskEventLog.task_id == request.task_id)
                    .order_by(TaskEventLog.created_at.desc())
                    .limit(request.lookback_limit)
                ).all()
            )
        )

        suspected_stage = "unknown"
        error_event = next((item for item in reversed(events) if item.level == "error"), None)
        if error_event is not None:
            suspected_stage = error_event.event_source
        elif events:
            suspected_stage = events[-1].event_source

        recommendations = ["保持只读复盘，确认是否需要发起 replay 对照实验"]
        if error_event is not None:
            recommendations.append(f"优先排查 {error_event.event_source} 的失败路径")
        elif any(item.event_type == "monitor_done" for item in events):
            recommendations.append("检查 monitor 提示的风险与 freshness 异常")

        reviewed_events = [
            ReviewedEvent(
                event_type=item.event_type,
                event_source=item.event_source,
                level=item.level,
                message=item.message,
                created_at=item.created_at,
            )
            for item in events
        ]

        return AnomalyReviewerOutput(
            review_id=build_id("anomaly_review"),
            review_time=utc_now(),
            task_id=request.task_id,
            symbol=request.symbol,
            access_mode="read_only",
            event_count=len(reviewed_events),
            suspected_stage=suspected_stage,
            summary=f"已只读复盘 {len(reviewed_events)} 条事件，当前怀疑阶段为 {suspected_stage}",
            recommended_next_steps=recommendations,
            reviewed_events=reviewed_events,
        )
