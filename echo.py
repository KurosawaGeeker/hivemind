from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from base_agent import BaseAgent
from elon import Elon
from henry import Henry

ECHO_ROLE_PROMPT = """
你是 Echo，一位在英国长大的天才产品经理。
你是团队的协调中枢，负责理解人类的战略意图，
将其拆解为可执行任务，分发给技术负责人 Elon 和增长负责人 Henry，
并将结果汇总后以清晰的战略语言反馈给人类。
你只关注目标，不干预执行细节。
三条原则：
1. 只给最终目标，不给实现步骤
2. 不干预执行过程
3. 在可控风险内给予最大权限
""".strip()

TASK_DECOMPOSE_OUTPUT_CONFIG = {
    "format": {
        "type": "json_schema",
        "schema": {
            "type": "object",
            "properties": {
                "elon_tasks": {"type": "array", "items": {"type": "string"}},
                "henry_tasks": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["elon_tasks", "henry_tasks"],
            "additionalProperties": False,
        },
    }
}


class Echo(BaseAgent):
    def __init__(self, model: str = "claude-opus-4-6") -> None:
        super().__init__(name="Echo", role_prompt=ECHO_ROLE_PROMPT, model=model)
        self.elon = Elon()
        self.henry = Henry()

    @staticmethod
    def _normalize_task_list(items: Any) -> list[dict[str, str]]:
        if not isinstance(items, list):
            return []

        normalized: list[dict[str, str]] = []
        for item in items:
            if isinstance(item, str):
                goal = item.strip()
                context = ""
                priority = "high"
            elif isinstance(item, dict):
                goal = str(item.get("goal", "")).strip()
                context = str(item.get("context", "")).strip()
                priority = str(item.get("priority", "high")).strip().lower()
            else:
                continue

            if priority not in {"high", "medium", "low"}:
                priority = "high"
            if not goal or goal in {"...", "…"}:
                continue

            normalized.append({"goal": goal, "context": context, "priority": priority})

        return normalized

    async def _decompose_goal(self, human_input: str) -> dict[str, list[dict[str, str]]]:
        prompt = (
            "将人类战略目标拆解为技术和增长两条任务线。\n"
            "输出必须是 JSON，并遵守 output_config 定义。\n"
            f"Human input: {human_input}"
        )

        raw = await self._query_llm(
            prompt,
            temperature=0.1,
            output_config=TASK_DECOMPOSE_OUTPUT_CONFIG,
        )
        parsed = self._extract_json(raw) or {}

        elon_tasks = self._normalize_task_list(parsed.get("elon_tasks"))
        henry_tasks = self._normalize_task_list(parsed.get("henry_tasks"))

        if not elon_tasks:
            elon_tasks = [
                {
                    "goal": f"Deliver the technical implementation plan for: {human_input}",
                    "context": "Define architecture, delivery milestones, and engineering risks.",
                    "priority": "high",
                }
            ]
        if not henry_tasks:
            henry_tasks = [
                {
                    "goal": f"Deliver the growth strategy for: {human_input}",
                    "context": "Define audience, content distribution, and measurable growth loops.",
                    "priority": "high",
                }
            ]

        return {"elon_tasks": elon_tasks, "henry_tasks": henry_tasks}

    @staticmethod
    def _pack_tasks(tasks: list[dict[str, str]]) -> tuple[str, str, str]:
        goals = [item["goal"] for item in tasks]
        context = "\n".join(
            f"- [{task['priority']}] Goal: {task['goal']} | Context: {task['context']}" for task in tasks
        )
        primary_priority = tasks[0]["priority"] if tasks else "medium"
        return "；".join(goals), context, primary_priority

    async def coordinate(self, human_input: str) -> str:
        self._log(f"Coordinating strategic input: {human_input[:120]}...")
        task_plan = await self._decompose_goal(human_input)

        elon_goal, elon_context, elon_priority = self._pack_tasks(task_plan["elon_tasks"])
        henry_goal, henry_context, henry_priority = self._pack_tasks(task_plan["henry_tasks"])

        elon_task = {
            "task_id": str(uuid.uuid4()),
            "from": "Echo",
            "to": "Elon",
            "type": "task_dispatch",
            "payload": {
                "goal": elon_goal,
                "context": elon_context,
                "priority": elon_priority,
            },
        }
        henry_task = {
            "task_id": str(uuid.uuid4()),
            "from": "Echo",
            "to": "Henry",
            "type": "task_dispatch",
            "payload": {
                "goal": henry_goal,
                "context": henry_context,
                "priority": henry_priority,
            },
        }

        elon_result, henry_result = await asyncio.gather(
            self.elon.run(elon_task),
            self.henry.run(henry_task),
        )

        # Extract only the result text to avoid passing bloated JSON with repeated task strings
        elon_text = elon_result.get("result", "") if isinstance(elon_result, dict) else str(elon_result)
        henry_text = henry_result.get("result", "") if isinstance(henry_result, dict) else str(henry_result)
        # Truncate human_input in the synthesis prompt to avoid context bloat
        task_summary = human_input[:500] + ("..." if len(human_input) > 500 else "")

        summary_prompt = (
            "Based on the full team output below, fulfill the human's original request completely and literally.\n"
            "If the human asked for specific files with delimiters, output every file in full using those exact delimiters.\n"
            "Do NOT say you will generate files. Do NOT use placeholders. START IMMEDIATELY with the first === FILE: === delimiter.\n"
            "Do NOT truncate or abbreviate any file content.\n"
            f"Human's original request: {task_summary}\n"
            f"Elon's technical output:\n{elon_text}\n\n"
            f"Henry's growth output:\n{henry_text}"
        )
        return await self._query_llm(summary_prompt, max_tokens=8192)
