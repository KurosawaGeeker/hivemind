from __future__ import annotations

import asyncio
import json
from typing import Any

from base_agent import BaseAgent

ELON_ROLE_PROMPT = """
你是 Elon，团队 CTO。
你的职责是把 Echo 派发的技术目标拆解为可执行方案，
并组织架构、评审测试、调试修复三个技术子代理并行执行。
你只关注技术交付质量、稳定性、可维护性。
""".strip()


class ArchitectAgent(BaseAgent):
    def __init__(self, model: str = "claude-haiku-4-5") -> None:
        super().__init__(
            name="Elon/Architecture",
            model=model,
            role_prompt=(
                "你是 Architecture 子代理。"
                "聚焦系统设计、模块拆分、依赖选择、风险与扩展性。"
            ),
        )


class ReviewAgent(BaseAgent):
    def __init__(self, model: str = "claude-haiku-4-5") -> None:
        super().__init__(
            name="Elon/Review",
            model=model,
            role_prompt=(
                "你是 Code Review & Testing 子代理。"
                "聚焦代码审查要点、测试策略、质量门禁与回归风险。"
            ),
        )


class DebugAgent(BaseAgent):
    def __init__(self, model: str = "claude-haiku-4-5") -> None:
        super().__init__(
            name="Elon/Debug",
            model=model,
            role_prompt=(
                "你是 Debug & Fix 子代理。"
                "聚焦故障定位、根因分析、修复步骤与验证方案。"
            ),
        )


class Elon(BaseAgent):
    def __init__(self, model: str = "claude-opus-4-6", sub_model: str = "claude-haiku-4-5") -> None:
        super().__init__(name="Elon", role_prompt=ELON_ROLE_PROMPT, model=model)
        self.architect = ArchitectAgent(model=sub_model)
        self.reviewer = ReviewAgent(model=sub_model)
        self.debugger = DebugAgent(model=sub_model)

    @staticmethod
    def _normalize_task(task: dict[str, Any]) -> tuple[str, str, str]:
        task_id = str(task.get("task_id", ""))
        payload = task.get("payload") if isinstance(task.get("payload"), dict) else {}

        goal = str(task.get("goal") or payload.get("goal") or "").strip()
        context = str(task.get("context") or payload.get("context") or "").strip()
        return task_id, goal, context

    def _build_subtasks(self, task_id: str, goal: str, context: str) -> list[tuple[BaseAgent, dict[str, str]]]:
        return [
            (
                self.architect,
                {
                    "task_id": task_id,
                    "from": "Elon",
                    "goal": f"Design technical architecture for: {goal}",
                    "context": context,
                },
            ),
            (
                self.reviewer,
                {
                    "task_id": task_id,
                    "from": "Elon",
                    "goal": f"Produce review and testing plan for: {goal}",
                    "context": context,
                },
            ),
            (
                self.debugger,
                {
                    "task_id": task_id,
                    "from": "Elon",
                    "goal": f"List likely failure modes and fixes for: {goal}",
                    "context": context,
                },
            ),
        ]

    async def run(self, task: dict[str, Any]) -> dict[str, str]:
        task_id, goal, context = self._normalize_task(task)
        self._log(f"Dispatching sub-agents for goal: {goal}")

        try:
            subtasks = self._build_subtasks(task_id=task_id, goal=goal, context=context)
            results = await asyncio.gather(*(agent.run(subtask) for agent, subtask in subtasks))

            summary_prompt = (
                "Synthesize the three technical tracks into a concise CTO report.\n"
                "Use headings: Architecture, Quality & Testing, Debug/Fix, Delivery Risks.\n"
                f"Goal: {goal}\n"
                f"Context: {context}\n"
                f"Sub-agent outputs: {json.dumps(results, ensure_ascii=False)}"
            )
            merged = await self._query_llm(summary_prompt)
            return {
                "task_id": task_id,
                "from": "Elon",
                "result": merged,
                "status": "done",
            }
        except Exception as exc:  # noqa: BLE001
            self._log(f"Error: {exc}")
            return {
                "task_id": task_id,
                "from": "Elon",
                "result": str(exc),
                "status": "error",
            }
