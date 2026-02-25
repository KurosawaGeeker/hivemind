# Architecture

## Overview

Hive Mind models a hierarchical product team as a tree of async agents. Each agent wraps an Anthropic Claude model and communicates via structured text.

## Agent Hierarchy

```
Echo (Coordinator)
├── Elon (CTO Lead)
│   ├── ArchitectAgent   — system design, tech stack decisions
│   ├── ReviewAgent      — code review, quality checks
│   └── DebugAgent       — error analysis, fix suggestions
└── Henry (CMO Lead)
    ├── CommunityAgent   — engagement strategy, community management
    ├── ContentAgent      — articles, tutorials, documentation
    └── AnalyticsAgent   — metrics, KPIs, data analysis
```

## Execution Flow

1. Human sends a goal string to `Echo.coordinate(human_input)`.
2. Echo calls the LLM to decompose the goal into a CTO task and a CMO task.
3. `asyncio.gather` runs `Elon.run(cto_task)` and `Henry.run(cmo_task)` in parallel.
4. Each lead agent further fans out to 3 sub-agents in parallel via `asyncio.gather`.
5. Each lead synthesizes its sub-agent outputs into a report.
6. Echo receives both reports and calls the LLM to produce a unified response.

## BaseAgent Contract

All agents inherit from `BaseAgent`, which provides:

| Method | Purpose |
|---|---|
| `_query_llm(system, user)` | Send a message to Claude. Retries up to 3 times with exponential backoff. |
| `_extract_text(response)` | Pull plain text from the API response. |
| `_extract_json(response)` | Parse structured JSON from the API response. |
| `reset_timeline()` | Clear the timeline trace buffer. |
| `get_timeline()` | Return a list of `{agent, action, duration_ms, timestamp}` entries. |

## Model Assignment

| Agent | Default Model | Rationale |
|---|---|---|
| Echo, Elon, Henry | Sonnet | Complex reasoning, synthesis, decomposition |
| All sub-agents | Haiku | Fast, cheap, focused single-task execution |

## Concurrency Model

All I/O is async. The framework uses `asyncio.gather` at two levels:

- Lead level: Elon and Henry run in parallel.
- Sub-agent level: Each lead's 3 sub-agents run in parallel.

This gives a maximum theoretical concurrency of 6 sub-agent LLM calls + 2 lead synthesis calls per request.

## Observability

Every `_query_llm` call appends to the agent's timeline. After `coordinate()` completes, call `echo.get_timeline()` to get a full trace of all agent activity with durations — useful for debugging latency and understanding execution order.
