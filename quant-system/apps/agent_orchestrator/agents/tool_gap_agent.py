"""工具缺口观察智能体。"""

from __future__ import annotations

from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.agent_orchestrator.schemas.tool_gap import ToolGapInput, ToolGapItem, ToolGapOutput
from shared.models.tables import TaskEventLog
from shared.utils.ids import build_id
from shared.utils.time import utc_now


class ToolGapAgent:
    """只汇总缺口并生成建议报告，不自动变更系统。"""

    GAP_RECOMMENDATIONS = {
        "tool_acl_denied": "检查角色白名单是否缺少必要只读工具",
        "tool_input_invalid": "补齐工具输入 schema 和调用参数校验",
        "tool_output_invalid": "修复工具输出 schema 或工具实现",
        "tool_runtime_failed": "补充工具稳定性保护和失败回退",
        "openclaw_agent_output_invalid": "收紧 OpenClaw agent 输出契约并增加示例",
    }

    def run(self, session: Session, request: ToolGapInput) -> ToolGapOutput:
        rows = list(
            session.scalars(
                select(TaskEventLog)
                .where(
                    TaskEventLog.event_type.in_(tuple(self.GAP_RECOMMENDATIONS.keys()))
                )
                .order_by(TaskEventLog.created_at.desc())
                .limit(request.lookback_limit)
            ).all()
        )
        counter = Counter(row.event_type for row in rows)
        gap_items = [
            ToolGapItem(code=event_type, count=count, recommendation=self.GAP_RECOMMENDATIONS[event_type])
            for event_type, count in counter.items()
        ]
        summary = "未发现近期工具缺口事件" if not gap_items else f"已汇总 {len(gap_items)} 类工具缺口，当前仅生成建议报告"
        return ToolGapOutput(
            report_id=build_id("tool_gap"),
            report_time=utc_now(),
            lookback_limit=request.lookback_limit,
            summary=summary,
            gap_items=gap_items,
        )
