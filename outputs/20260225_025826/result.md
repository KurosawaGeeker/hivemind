# 任务输出

**输入**: 为以下这个真实的 Hive Mind 多 Agent 项目生成完整的开源发布材料。

项目源码如下：

### base_agent.py
```python
﻿from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any

from dotenv import load_dotenv

# --- Timeline collector ---
_TIMELINE: list[dict] = []
_START_TIME: float = 0.0


def reset_timeline() -> None:
    global _START_TIME
    _TIMELINE.clear()
    _START_TIME = time.time()


def get_timeline() -> list[dict]:
    return list(_TIMELINE)


def _record(agent: str, event: str, detail: str = "") -> None:
    elapsed = round(time.time() - _START_TIME, 2) if _START_TIME else 0.0
    _TIMELINE.append({"t": elapsed, "agent": agent, "event": event, "detail": detail})

try:
    import httpx
    from anthropic import AsyncAnthropic, APIConnectionError, APITimeoutError, InternalServerError
except ImportError:  # pragma: no cover
    AsyncAnthropic = None
    httpx = None
    APIConnectionError = APITimeoutError = InternalServerError = Exception

_RETRY_DELAYS = [5, 20]  # seconds between attempts 1→2 and 2→3

SHARED_BASE_PROMPT = """
You are one member of a multi-agent Hive Mind team.
Work with high autonomy, stay inside your role boundaries, and keep outputs concise, actionable, and reliable.
When context is uncertain, make the safest useful assumption and state it.
""".strip()


class BaseAgent:
    def __init__(self, name: str, role_prompt: str, model: str, tools: list | None = None) -> None:
        load_dotenv()
        self.name = name
        self.role_prompt = role_prompt.strip()
        self.model = model
        self.tools = tools or []

        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        base_url = os.getenv("ANTHROPIC_BASE_URL", "").strip()

        if AsyncAnthropic and api_key:
            client_kwargs: dict[str, Any] = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            # Bypass system proxy (Clash/VPN) to connect directly to the API endpoint
            if httpx:
                client_kwargs["http_client"] = httpx.AsyncClient(
                    transport=httpx.AsyncHTTPTransport(proxy=None),
                    timeout=120,
                )
            self.client = AsyncAnthropic(**client_kwargs)
        else:
            self.client = None

    def _log(self, message: str) -> None:
        print(f"[{self.name}] {message}")
        _record(self.name, message)

    @staticmethod
    def _extract_text(content: Any) -> str:
        chunks: list[str] = []
        for item in content:
            if getattr(item, "type", "") == "text":
                chunks.append(getattr(item, "text", ""))
        return "\n".join(chunk for chunk in chunks if chunk).strip()

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any] | None:
        text = (text or "").strip()
        if not text:
            return None

        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None

        candidate = text[start : end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return None
        return None

    async def _query_llm(
        self,
        user_prompt: str,
        *,
        extra_system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int | None = None,
        output_config: dict[str, Any] | None = None,
    ) -> str:
        if not self.client:
            if not AsyncAnthropic:
                self._log("anthropic SDK missing; using offline fallback response.")
            else:
                self._log("ANTHROPIC_API_KEY missing; using offline fallback response.")
            return f"[offline:{self.name}] {user_prompt[:600]}"

        system_prompt = "\n\n".join(
            part
            for part in (SHARED_BASE_PROMPT, self.role_prompt, extra_system_prompt.strip())
            if part
        )
        token_limit = max_tokens if max_tokens is not None else (4096 if "opus" in self.model else 2048)

        request_payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": token_limit,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        # Opus main agents use adaptive thinking; Haiku sub-agents must not send thinking.
        if "opus" in self.model:
            request_payload["thinking"] = {"type": "adaptive"}
        else:
            request_payload["temperature"] = temperature

        if output_config:
            request_payload["output_config"] = output_config

        t0 = time.time()
        _record(self.name, "调用 LLM", f"model={self.model} max_tokens={token_limit}")

        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                response = await self.client.messages.create(**request_payload)
                break
            except (APITimeoutError, APIConnectionError, InternalServerError) as exc:
                last_exc = exc
                if attempt < 2:
                    delay = _RETRY_DELAYS[attempt]
                    self._log(f"请求失败，{delay}s 后重试 ({attempt+1}/2)... [{exc.__class__.__name__}]")
                    await asyncio.sleep(delay)
        else:
            raise last_exc  # type: ignore[misc]

        _record(self.name, "LLM 响应完成", f"用时约 {round(time.time() - t0, 1)}s")
        return self._extract_text(response.content)

    async def run(self, task: dict[str, Any]) -> dict[str, str]:
        task_id = str(task.get("task_id", ""))
        goal = str(task.get("goal", "")).strip()
        context = str(task.get("context", "")).strip()

        self._log(f"Received task: {goal or '(empty goal)'}")
        prompt = (
            "Complete the task using your role.\n"
            f"Goal: {goal}\n"
            f"Context: {context}\n"
            "Return a direct, execution-ready result."
        )

        try:
            result = await self._query_llm(prompt)
            return {
                "task_id": task_id,
                "from": self.name,
                "result": result,
                "status": "done",
            }
        except Exception as exc:  # noqa: BLE001
            self._log(f"Error: {exc}")
            return {
                "task_id": task_id,
                "from": self.name,
                "result": str(exc),
                "status": "error",
            }

```

### echo.py
```python
﻿from __future__ import annotations

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
        self._log(f"Coordinating strategic input: {human_input}")
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
            "If the human asked for a strategic summary, output that.\n"
            "Do NOT truncate, abbreviate, or replace file content with placeholders.\n"
            f"Human's original request: {task_summary}\n"
            f"Elon's technical output:\n{elon_text}\n\n"
            f"Henry's growth output:\n{henry_text}"
        )
        return await self._query_llm(summary_prompt, max_tokens=8192)

```

### elon.py
```python
﻿from __future__ import annotations

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

```

### henry.py
```python
﻿from __future__ import annotations

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

```

### main.py
```python
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime

# Fix Windows GBK encoding for both stdin and stdout
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")

from base_agent import get_timeline, reset_timeline
from echo import Echo


def _split_files(result: str) -> dict[str, str]:
    """Parse '=== FILE: name ===' delimiters into separate file contents."""
    files: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []

    for line in result.splitlines():
        stripped = line.strip()
        if stripped.startswith("=== FILE:") and stripped.endswith("==="):
            if current_name is not None:
                files[current_name] = "\n".join(current_lines).strip()
            current_name = stripped[9:-3].strip()
            current_lines = []
        else:
            if current_name is not None:
                current_lines.append(line)

    if current_name is not None:
        files[current_name] = "\n".join(current_lines).strip()

    return files


def _write_outputs(human_input: str, result: str, run_dir: str) -> None:
    os.makedirs(run_dir, exist_ok=True)

    # Try to split into named files; fall back to single result.md
    files = _split_files(result)
    if files:
        for filename, content in files.items():
            # Support subdirectories like .github/ISSUE_TEMPLATE/bug_report.yml
            filepath = os.path.join(run_dir, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content + "\n")
        print(f"[输出] 已保存 {len(files)} 个文件到 {run_dir}/")
    else:
        with open(os.path.join(run_dir, "result.md"), "w", encoding="utf-8") as f:
            f.write(f"# 任务输出\n\n**输入**: {human_input}\n\n---\n\n{result}\n")
        print(f"[输出] result.md 已保存到 {run_dir}/")

    # Always write timeline and original task
    timeline = get_timeline()
    lines = [
        "# Hive Mind 行动时间线\n",
        f"**任务**: {human_input}\n",
        f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        "\n| 耗时(s) | Agent | 事件 | 备注 |\n",
        "|---------|-------|------|------|\n",
    ]
    for e in timeline:
        detail = e["detail"].replace("|", "\\|") if e["detail"] else ""
        lines.append(f"| +{e['t']} | {e['agent']} | {e['event']} | {detail} |\n")
    with open(os.path.join(run_dir, "timeline.md"), "w", encoding="utf-8") as f:
        f.writelines(lines)
    with open(os.path.join(run_dir, "task.txt"), "w", encoding="utf-8") as f:
        f.write(human_input)


async def _run_once(echo: Echo, human_input: str) -> None:
    reset_timeline()
    result = await echo.coordinate(human_input)
    print(f"\nEcho > {result}\n")
    run_dir = os.path.join("outputs", datetime.now().strftime("%Y%m%d_%H%M%S"))
    _write_outputs(human_input, result, run_dir)


def _load_prior_output(prior_dir: str) -> dict[str, str]:
    """Recursively read all output files, skipping metadata."""
    skip = {"timeline.md", "task.txt"}
    files: dict[str, str] = {}
    for root, _, filenames in os.walk(prior_dir):
        for fname in filenames:
            if fname in skip:
                continue
            abs_path = os.path.join(root, fname)
            rel_path = os.path.relpath(abs_path, prior_dir).replace("\\", "/")
            with open(abs_path, encoding="utf-8") as f:
                files[rel_path] = f.read()
    return files


def _build_refine_prompt(prior_files: dict[str, str], original_task: str, feedback: str) -> str:
    parts = [
        "以下是团队上一轮的输出成果，请在保留优点的基础上，根据改进反馈重新输出全部文件。",
        "每个文件用 === FILE: 文件名 === 作为分隔符开头，不要省略任何文件。",
        "",
        f"原始任务：\n{original_task}" if original_task else "",
        f"\n改进反馈：\n{feedback}" if feedback else "\n改进反馈：（无具体反馈，请自行审视并优化）",
        "\n上一轮产出：",
    ]
    for filename, content in prior_files.items():
        parts.append(f"\n=== FILE: {filename} ===\n{content}")
    return "\n".join(p for p in parts if p is not None)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Hive Mind — multi-agent coordinator")
    parser.add_argument("--task", "-t", type=str, default=None,
                        help="Run a single task non-interactively and exit")
    parser.add_argument("--refine", type=str, default=None,
                        help="Path to prior output dir to refine")
    parser.add_argument("--feedback", type=str, default="",
                        help="Specific improvement feedback for --refine mode")
    args = parser.parse_args()

    echo = Echo()

    if args.task:
        print(f"[Hive Mind] 无人值守模式，任务: {args.task}")
        await _run_once(echo, args.task)
        return

    if args.refine:
        prior_files = _load_prior_output(args.refine)
        task_file = os.path.join(args.refine, "task.txt")
        original_task = open(task_file, encoding="utf-8").read().strip() if os.path.exists(task_file) else ""
        refine_prompt = _build_refine_prompt(prior_files, original_task, args.feedback)
        print(f"[Hive Mind] Refine 模式，基于: {args.refine}，载入 {len(prior_files)} 个文件")
        await _run_once(echo, refine_prompt)
        return

    # Interactive REPL
    print("Hive Mind 已启动。输入你的战略目标：")
    while True:
        human_input = input("Human > ").strip()
        if human_input.lower() in ("exit", "quit"):
            print("Hive Mind 已退出。")
            break
        if not human_input:
            continue
        await _run_once(echo, human_input)


if __name__ == "__main__":
    asyncio.run(main())

```

要求输出6个文件，每个文件用 === FILE: 文件名 === 作为分隔符开头。
文件清单：README.md、ARCHITECTURE.md、CONTRIBUTING.md、.github/ISSUE_TEMPLATE/bug_report.yml、.github/ISSUE_TEMPLATE/feature_request.yml、LAUNCH_PLAN.md

技术文档（README、ARCHITECTURE、CONTRIBUTING）必须基于上方真实源码，确保模块名、函数名、类名与代码完全一致。

---


