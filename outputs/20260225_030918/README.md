<p align="center">
  <img src="https://raw.githubusercontent.com/hivemind-agents/hivemind/main/.github/assets/logo.png" alt="Hive Mind" width="200">
</p>

<h1 align="center">Hive Mind</h1>

<p align="center">
  <strong>A multi-agent orchestration framework built on Anthropic Claude</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/hivemind-agents/"><img src="https://img.shields.io/pypi/v/hivemind-agents" alt="PyPI"></a>
  <a href="https://github.com/hivemind-agents/hivemind/actions"><img src="https://img.shields.io/github/actions/workflow/status/hivemind-agents/hivemind/ci.yml?branch=main" alt="CI"></a>
  <a href="https://github.com/hivemind-agents/hivemind/blob/main/LICENSE"><img src="https://img.shields.io/github/license/hivemind-agents/hivemind" alt="License"></a>
  <a href="https://github.com/hivemind-agents/hivemind/stargazers"><img src="https://img.shields.io/github/stars/hivemind-agents/hivemind" alt="Stars"></a>
  <a href="https://pypi.org/project/hivemind-agents/"><img src="https://img.shields.io/pypi/dm/hivemind-agents" alt="Downloads"></a>
</p>

---

Hive Mind is a Python framework for building hierarchical multi-agent systems powered by [Anthropic Claude](https://www.anthropic.com/). It models a real product team — a coordinator (Echo), a CTO (Elon), and a CMO (Henry) — each backed by specialized sub-agents that run in parallel via `asyncio`.

## Why Hive Mind?

- **Hierarchical orchestration** — Coordinator decomposes goals, delegates to leads, leads fan out to specialist sub-agents, results roll up automatically.
- **Parallel by default** — All independent sub-agent calls run concurrently with `asyncio.gather`.
- **Built-in resilience** — Every LLM call retries 3 times with exponential backoff.
- **Timeline tracing** — Full observability of every agent call via `get_timeline()`.
- **Minimal surface area** — Four files, one base class, zero magic.

## Architecture

```
Human
  │
  ▼
┌─────────────────────────────────────────────┐
│  Echo (Coordinator · Sonnet)                │
│  coordinate(human_input)                    │
│    ├─ LLM: decompose into tasks             │
│    ├─ asyncio.gather(elon.run, henry.run)   │
│    └─ LLM: synthesize final report          │
├─────────────────────┬───────────────────────┤
│  Elon (CTO · Sonnet)│  Henry (CMO · Sonnet) │
│  run()              │  run()                │
│   ├─ Architect (H)  │   ├─ Community (H)    │
│   ├─ Review   (H)   │   ├─ Content  (H)     │
│   └─ Debug    (H)   │   └─ Analytics(H)     │
└─────────────────────┴───────────────────────┘
  (H) = Haiku sub-agent
```

## Quick Start (5 minutes)

### 1. Install

```bash
pip install hivemind-agents
```

Or from source:

```bash
git clone https://github.com/hivemind-agents/hivemind.git
cd hivemind
pip install -e ".[dev]"
```

### 2. Set your API key

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

### 3. Run

```python
import asyncio
from hivemind import Echo

async def main():
    echo = Echo()
    result = await echo.coordinate(
        "Design a landing page for our new developer tool"
    )
    print(result)

asyncio.run(main())
```

### 4. Inspect the timeline

```python
for entry in echo.get_timeline():
    print(f"[{entry['agent']}] {entry['action']} — {entry['duration_ms']}ms")
```

## Configuration

| Environment Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | — | Your Anthropic API key |
| `HIVEMIND_COORDINATOR_MODEL` | No | `claude-sonnet-4-20250514` | Model for Echo/Elon/Henry |
| `HIVEMIND_SUBAGENT_MODEL` | No | `claude-haiku-4-20250514` | Model for sub-agents |
| `HIVEMIND_MAX_RETRIES` | No | `3` | LLM call retry count |
| `HIVEMIND_LOG_LEVEL` | No | `INFO` | Logging verbosity |

## Extending

Create your own agent by subclassing `BaseAgent`:

```python
from hivemind.base_agent import BaseAgent

class MyAgent(BaseAgent):
    async def run(self, task: str) -> str:
        response = await self._query_llm(
            system="You are a specialist in X.",
            user=task,
        )
        return self._extract_text(response)
```

## Project Structure

```
hivemind/
├── __init__.py
├── base_agent.py      # BaseAgent base class with LLM, retry, timeline
├── echo.py            # Echo coordinator — task decomposition & synthesis
├── elon.py            # Elon CTO — Architect / Review / Debug sub-agents
├── henry.py           # Henry CMO — Community / Content / Analytics sub-agents
tests/
├── test_base_agent.py
├── test_echo.py
├── test_elon.py
└── test_henry.py
```

## Contributing

We welcome contributions of all sizes. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT](LICENSE) © 2026 Hive Mind Contributors
