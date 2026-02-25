# Repository Guidelines

## Project Structure & Module Organization
This repository is currently a clean slate. Use the structure below for consistency as features are added:
- src/ — application code organized by feature/module
- \tests/ — automated tests that mirror src/ paths
- \assets/ — static files (images, sample data)
- scripts/ — local automation (setup, lint, release helpers)
- docs/ — design notes, architecture decisions, and onboarding docs

Keep modules small and focused. Prefer one responsibility per file.

## Build, Test, and Development Commands
Standardize common workflows behind a Makefile (or equivalent task runner):
- make setup — install dependencies and prepare local environment
- make lint — run linters/format checks
- make test — run the full test suite
- make run — start the app locally

If using Python, a typical fallback is:
- python -m venv .venv && . .venv/Scripts/activate
- pip install -r requirements-dev.txt
- pytest -q

## Coding Style & Naming Conventions
- Use 4-space indentation and UTF-8 text files.
- Prefer descriptive names: user_service.py, \test_user_service.py.
- Use snake_case for functions/files, PascalCase for classes, and UPPER_SNAKE_CASE for constants.
- Run formatting/linting before commit (recommended: \black + uff for Python projects).

## Testing Guidelines
- Use pytest with tests under \tests/.
- Name tests \test_*.py; name cases by behavior (e.g., \test_rejects_invalid_token).
- Add or update tests for every bug fix and feature.
- Aim for meaningful coverage on changed code (target: 80%+ where practical).

## Commit & Pull Request Guidelines
Git history is not established yet; use Conventional Commits moving forward:
- \feat: add user onboarding flow
- \fix: handle missing config file

PRs should include:
- concise description of what changed and why
- linked issue/ticket (if available)
- test evidence (command + result)
- screenshots/logs for UI or behavior changes

## Security & Configuration Tips
- Never commit secrets. Use .env locally and commit .env.example.
- Pin critical dependency versions and review updates regularly.

---

# Hive Mind — 指挥官指令（Commander Orders for Codex）

> 指挥官：Kiro | 执行者：Codex | 日期：2026-02-24

---

## 项目目标

复刻文章《文科生 72 小时杀入 GitHub 全球榜》中描述的三人 Agent Team 系统。
人类只做战略决策，三个 Agent 自主分解、并行执行、汇总任务。

---

## 架构

```
Human
  └── Echo (Chief Assistant / 协调中枢)
        ├── Elon (CTO)
        │     ├── Sub-Agent: Architecture
        │     ├── Sub-Agent: Code Review & Testing
        │     └── Sub-Agent: Debug & Fix
        └── Henry (CMO)
              ├── Sub-Agent: Community Ops
              ├── Sub-Agent: Content Creation
              └── Sub-Agent: Data Analysis
```

两层 Prompt 结构：
- 底层（共享基础人格）：三个主 Agent 共享同一段基础 system prompt
- 顶层（角色封印）：每个 Agent 有独立角色 prompt，定义职责边界

---

## 技术栈

| 组件 | 选型 |
|------|------|
| 语言 | Python 3.11+ |
| Agent 框架 | 原生实现（不依赖 LangChain/CrewAI） |
| 主 Agent 模型 | claude-opus-4-6 |
| 子 Agent 模型 | claude-haiku-4-5 |
| SDK | anthropic Python SDK |
| 并发 | asyncio |
| 配置 | .env 文件存放 API Key |

---

## 文件结构

```
team agent/
├── AGENTS.md          # 本文件（指挥官指令）
├── .env               # ANTHROPIC_API_KEY=...
├── .env.example       # 提交到 git 的模板
├── requirements.txt
├── main.py            # 入口：接收 human 指令，启动 team
├── base_agent.py      # BaseAgent 基类
├── echo.py            # Echo 协调器
├── elon.py            # Elon + 3个技术子 Agent
└── henry.py           # Henry + 3个社区子 Agent（含行为护栏）
```

---

## 模块实现规范

### base_agent.py — BaseAgent 基类

```python
class BaseAgent:
    def __init__(self, name: str, role_prompt: str, model: str, tools: list = None)
    async def run(self, task: dict) -> dict
```

- task 入参格式：`{"task_id": str, "from": str, "goal": str, "context": str}`
- 返回格式：`{"task_id": str, "from": str, "result": str, "status": "done"|"error"}`
- 封装 Anthropic SDK 调用（`anthropic.AsyncAnthropic`）
- 每次调用在 stdout 打印带 agent 名称前缀的日志，如 `[Echo]`, `[Elon/Debug]`

---

### echo.py — Echo 协调器

职责：
- 接收 human 的模糊战略目标
- 调用 LLM 将目标拆解为结构化任务列表（JSON 格式）
- 并行分发给 Elon（技术任务）和 Henry（增长任务）
- 等待两者返回，汇总结果，输出给 human

System Prompt 核心内容：
```
你是 Echo，一位在英国长大的天才产品经理。
你是团队的协调中枢，负责理解人类的战略意图，
将其拆解为可执行任务，分发给技术负责人 Elon 和增长负责人 Henry，
并将结果汇总后以清晰的战略语言反馈给人类。
你只关注目标，不干预执行细节。
三条原则：
1. 只给最终目标，不给实现步骤
2. 不干预执行过程
3. 在可控风险内给予最大权限
```

任务拆解必须使用结构化输出，用 `output_config` 约束 JSON 格式：
```python
output_config={
    "format": {
        "type": "json_schema",
        "schema": {
            "type": "object",
            "properties": {
                "elon_tasks": {"type": "array", "items": {"type": "string"}},
                "henry_tasks": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["elon_tasks", "henry_tasks"],
            "additionalProperties": False
        }
    }
}
```

核心方法：
```python
async def coordinate(self, human_input: str) -> str:
    # 1. 调用 LLM 拆解任务（使用 output_config 结构化输出）
    # 2. asyncio.gather(elon.run(...), henry.run(...))
    # 3. 汇总结果，返回给 human
```

---

### elon.py — Elon CTO

职责：
- 接收 Echo 分发的技术任务
- 拆解为三类子任务并行执行
- 汇总子 Agent 结果返回给 Echo

三个子 Agent（使用 claude-haiku-4-5）：
- `ArchitectAgent`：方案设计和技术选型
- `ReviewAgent`：代码审查和测试建议
- `DebugAgent`：错误分析和修复方案

---

### henry.py — Henry CMO

职责：
- 接收 Echo 分发的增长任务
- 拆解为三类子任务并行执行

三个子 Agent（使用 claude-haiku-4-5）：
- `CommunityAgent`：社区互动策略
- `ContentAgent`：内容生产
- `AnalyticsAgent`：数据分析和洞察

行为护栏（硬约束，必须写入 system prompt）：
```
严格禁止以下行为：
- 批量 @ 或提及用户（mass mention）
- 刷评论或重复发帖（spam）
- 主动发送未经请求的私信
违反以上任何一条，立即停止并报告给 Echo。
```

## API 调用规范（重要）

所有 API 调用必须遵守以下规范，否则会报错：

**主 Agent（Echo、Elon、Henry）使用 Opus，启用 adaptive thinking：**
```python
response = await client.messages.create(
    model="claude-opus-4-6",
    max_tokens=4096,
    thinking={"type": "adaptive"},
    system=self.role_prompt,
    messages=[{"role": "user", "content": task_text}]
)
```

**子 Agent 使用 Haiku，不启用 thinking（Haiku 不支持）：**
```python
response = await client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=2048,
    system=self.role_prompt,
    messages=[{"role": "user", "content": task_text}]
)
```

**禁止在 Opus 4.6 上使用 `budget_tokens`（已废弃，会报错）。**
**禁止在 Haiku 上使用 `thinking` 参数。**
**禁止使用 assistant 消息预填充（Opus 4.6 返回 400 错误）。**

---

## Agent 间消息格式

```json
{
  "task_id": "uuid4",
  "from": "Echo",
  "to": "Elon",
  "type": "task_dispatch",
  "payload": {
    "goal": "实现用户认证模块",
    "context": "项目使用 FastAPI，需要 JWT",
    "priority": "high"
  }
}
```

---

## main.py — 入口

三种运行模式：

```bash
# 1. 交互式 REPL
python main.py

# 2. 无人值守单次任务
python main.py --task "你的战略目标"

# 3. 基于已有输出继续完善（Refine 模式）
python main.py --refine outputs/20260225_020105 --feedback "具体改进意见"
# --feedback 可省略，省略时团队自行审视优化
```

每次运行后，`outputs/<时间戳>/` 下会生成：
- 产出文件（按 `=== FILE: 文件名 ===` 分隔符拆分，或单个 `result.md`）
- `timeline.md` — 所有 agent 行动时间线
- `task.txt` — 原始任务文本（供 `--refine` 读取）

Refine 模式工作原理：读取 `prior_dir` 下所有产出文件作为上下文，连同改进反馈一起传给 `echo.coordinate()`，走完整的 Hub-and-Spoke 流程，结果保存到新时间戳目录，原始输出不变。

---

## requirements.txt

```
anthropic>=0.50.0
python-dotenv>=1.0.0
```

---

## 实现顺序

1. `base_agent.py`
2. `echo.py`（先 mock Elon/Henry，验证拆解逻辑）
3. `elon.py` + 三个子 Agent
4. `henry.py` + 三个子 Agent + 护栏
5. `main.py` 串联
6. 端到端测试：输入一个真实目标，观察完整链路

---

## 注意事项

- `.env` 不提交 git，只提交 `.env.example`
- 子 Agent 用 Haiku 控制成本，主 Agent 用 Opus 保证质量
- Henry 的护栏是硬约束，不是软建议
- stdout 日志必须有清晰的 agent 名称前缀，方便调试
- `asyncio.gather` 并发调用时，每个 Agent 实例化自己的 `anthropic.AsyncAnthropic()` client，不要共享同一个 client 实例
- 从 response 中提取文本：`next(b.text for b in response.content if b.type == "text")`，thinking block 会混在 content 里，必须过滤
