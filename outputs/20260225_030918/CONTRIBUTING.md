# Contributing to Hive Mind

Thanks for your interest in contributing! This guide will get you set up.

## Development Setup

```bash
git clone https://github.com/hivemind-agents/hivemind.git
cd hivemind
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Workflow

1. Fork the repo and create a branch from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```
2. Make your changes. Add or update tests as needed.
3. Run the checks:
   ```bash
   ruff check .
   mypy hivemind
   pytest --cov
   ```
4. Commit with a clear message following [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat: add timeout parameter to BaseAgent._query_llm
   fix: handle empty response in _extract_json
   docs: update quick start example
   ```
5. Open a Pull Request against `main`.

## Code Style

- We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.
- Type hints are required on all public APIs.
- Docstrings follow Google style.

## Adding a New Agent

1. Create `hivemind/your_agent.py` subclassing `BaseAgent`.
2. Implement `async def run(self, task: str) -> str`.
3. Add tests in `tests/test_your_agent.py`.
4. Export from `hivemind/__init__.py`.

## Adding a New Sub-Agent

Sub-agents are lightweight specialists invoked by a lead agent (Elon or Henry). They follow the same `BaseAgent` pattern but default to the Haiku model.

## Tests

- All tests use `pytest` with `pytest-asyncio`.
- Mock the Anthropic client for unit tests — never call the real API in CI.
- Aim for >80% coverage on new code.

## Pull Request Checklist

- [ ] Tests pass (`pytest --cov`)
- [ ] Linter passes (`ruff check .`)
- [ ] Type checker passes (`mypy hivemind`)
- [ ] Docstrings added/updated
- [ ] CHANGELOG.md updated (if user-facing change)

## Issue Response SLA

We aim to triage new issues within 24 hours. First-time contributors get priority review.

## Code of Conduct

This project follows our [Code of Conduct](CODE_OF_CONDUCT.md). Be kind, be constructive.
