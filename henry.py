from __future__ import annotations

import asyncio
import json
from typing import Any

from base_agent import BaseAgent

HENRY_GUARDRAIL_PROMPT = """
严格禁止以下行为：
- 批量 @ 或提及用户（mass mention）
- 刷评论或重复发帖（spam）
- 主动发送未经请求的私信
违反以上任何一条，立即停止并报告给 Echo。
""".strip()

HENRY_ROLE_PROMPT = f"""
你是 Henry，团队 CMO。
你负责增长策略执行：社区运营、内容生产、数据分析。
输出要可落地、可衡量、可复盘。
{HENRY_GUARDRAIL_PROMPT}
""".strip()


class CommunityAgent(BaseAgent):
    def __init__(self, model: str = "claude-haiku-4-5") -> None:
        super().__init__(
            name="Henry/Community",
            model=model,
            role_prompt=(
                "你是 Community Ops 子代理。"
                "给出合规社区增长动作、节奏、互动方案。\n"
                f"{HENRY_GUARDRAIL_PROMPT}"
            ),
        )


class ContentAgent(BaseAgent):
    def __init__(self, model: str = "claude-haiku-4-5") -> None:
        super().__init__(
            name="Henry/Content",
            model=model,
            role_prompt=(
                "你是 Content Creation 子代理。"
                "输出内容主题、框架、发布计划和 CTA。\n"
                f"{HENRY_GUARDRAIL_PROMPT}"
            ),
        )


class AnalyticsAgent(BaseAgent):
    def __init__(self, model: str = "claude-haiku-4-5") -> None:
        super().__init__(
            name="Henry/Analytics",
            model=model,
            role_prompt=(
                "你是 Data Analysis 子代理。"
                "定义指标、实验、监控与策略洞察。\n"
                f"{HENRY_GUARDRAIL_PROMPT}"
            ),
        )


class Henry(BaseAgent):
    def __init__(self, model: str = "claude-opus-4-6", sub_model: str = "claude-haiku-4-5") -> None:
        super().__init__(name="Henry", role_prompt=HENRY_ROLE_PROMPT, model=model)
        self.community = CommunityAgent(model=sub_model)
        self.content = ContentAgent(model=sub_model)
        self.analytics = AnalyticsAgent(model=sub_model)

    @staticmethod
    def _normalize_task(task: dict[str, Any]) -> tuple[str, str, str]:
        task_id = str(task.get("task_id", ""))
        payload = task.get("payload") if isinstance(task.get("payload"), dict) else {}

        goal = str(task.get("goal") or payload.get("goal") or "").strip()
        context = str(task.get("context") or payload.get("context") or "").strip()
        return task_id, goal, context

    @staticmethod
    def _violates_guardrails(goal: str, context: str) -> bool:
        text = f"{goal}\n{context}".lower()
        blocked_terms = [
            "mass mention",
            "bulk mention",
            "spam",
            "repeat post",
            "unsolicited dm",
            "cold dm",
            "批量@",
            "刷评论",
            "私信轰炸",
        ]
        return any(term in text for term in blocked_terms)

    async def run(self, task: dict[str, Any]) -> dict[str, str]:
        task_id, goal, context = self._normalize_task(task)
        self._log(f"Dispatching sub-agents for goal: {goal}")

        if self._violates_guardrails(goal, context):
            message = "Guardrail violation detected. Execution stopped and escalated to Echo."
            self._log(message)
            return {
                "task_id": task_id,
                "from": "Henry",
                "result": message,
                "status": "error",
            }

        try:
            subtasks = [
                (
                    self.community,
                    {
                        "task_id": task_id,
                        "from": "Henry",
                        "goal": f"Create community operations plan for: {goal}",
                        "context": context,
                    },
                ),
                (
                    self.content,
                    {
                        "task_id": task_id,
                        "from": "Henry",
                        "goal": f"Create content strategy for: {goal}",
                        "context": context,
                    },
                ),
                (
                    self.analytics,
                    {
                        "task_id": task_id,
                        "from": "Henry",
                        "goal": f"Create analytics plan for: {goal}",
                        "context": context,
                    },
                ),
            ]
            results = await asyncio.gather(*(agent.run(subtask) for agent, subtask in subtasks))

            summary_prompt = (
                "Synthesize the three growth tracks into a concise CMO report.\n"
                "Use headings: Community, Content, Analytics, Risks.\n"
                f"Goal: {goal}\n"
                f"Context: {context}\n"
                f"Sub-agent outputs: {json.dumps(results, ensure_ascii=False)}"
            )
            merged = await self._query_llm(summary_prompt)
            return {
                "task_id": task_id,
                "from": "Henry",
                "result": merged,
                "status": "done",
            }
        except Exception as exc:  # noqa: BLE001
            self._log(f"Error: {exc}")
            return {
                "task_id": task_id,
                "from": "Henry",
                "result": str(exc),
                "status": "error",
            }
