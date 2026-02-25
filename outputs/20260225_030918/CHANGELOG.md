# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-02-24

### Added
- `BaseAgent` base class with `_query_llm()` (3-retry with exponential backoff), `_extract_text()`, `_extract_json()`.
- Timeline tracing via `reset_timeline()` / `get_timeline()` on every agent.
- `Echo` coordinator agent with `coordinate(human_input)` — LLM task decomposition, parallel delegation, LLM synthesis.
- `Elon` CTO agent with parallel `ArchitectAgent`, `ReviewAgent`, `DebugAgent` sub-agents (Haiku).
- `Henry` CMO agent with parallel `CommunityAgent`, `ContentAgent`, `AnalyticsAgent` sub-agents (Haiku).
- Full async execution via `asyncio.gather`.
- Environment-based configuration (model selection, retry count, log level).
- CI pipeline with Ruff, mypy, pytest, and coverage gate.
- PyPI packaging via `hatchling`.

[Unreleased]: https://github.com/hivemind-agents/hivemind/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/hivemind-agents/hivemind/releases/tag/v0.1.0
