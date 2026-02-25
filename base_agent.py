from __future__ import annotations

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
