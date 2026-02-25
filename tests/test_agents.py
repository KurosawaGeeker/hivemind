import asyncio

from echo import Echo
from henry import Henry


def test_henry_guardrail_blocks_mass_mention() -> None:
    henry = Henry()
    result = asyncio.run(
        henry.run(
            {
                "task_id": "t-1",
                "from": "Echo",
                "goal": "Run a mass mention campaign on every post",
                "context": "Push growth quickly",
            }
        )
    )

    assert result["status"] == "error"
    assert "Guardrail violation" in result["result"]


def test_echo_decompose_falls_back_on_invalid_json(monkeypatch) -> None:
    echo = Echo()

    async def fake_query_llm(*_args, **_kwargs) -> str:
        return "not a json response"

    monkeypatch.setattr(echo, "_query_llm", fake_query_llm)

    plan = asyncio.run(echo._decompose_goal("Build an AI coding app"))

    assert plan["elon_tasks"]
    assert plan["henry_tasks"]
    assert plan["elon_tasks"][0]["priority"] == "high"


def test_echo_decompose_uses_output_config(monkeypatch) -> None:
    echo = Echo()
    call_kwargs = {}

    async def fake_query_llm(*_args, **kwargs) -> str:
        call_kwargs.update(kwargs)
        return '{"elon_tasks": ["Build auth module"], "henry_tasks": ["Launch content plan"]}'

    monkeypatch.setattr(echo, "_query_llm", fake_query_llm)

    plan = asyncio.run(echo._decompose_goal("Ship v1"))

    assert "output_config" in call_kwargs
    assert plan["elon_tasks"][0]["goal"] == "Build auth module"
    assert plan["henry_tasks"][0]["goal"] == "Launch content plan"
