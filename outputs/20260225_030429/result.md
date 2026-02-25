# 任务输出

**输入**: 为 Hive Mind 这个 Python 多 Agent 项目生成完整的开源发布材料。

项目结构：
- base_agent.py：BaseAgent 基类，封装 anthropic.AsyncAnthropic，含 _query_llm()（重试3次）、_extract_text()、_extract_json()、reset_timeline()/get_timeline() 时间线追踪
- echo.py：Echo(BaseAgent) 协调器，coordinate(human_input) 方法：LLM 拆解任务 → asyncio.gather(elon.run, henry.run) → LLM 合成结果
- elon.py：Elon(BaseAgent) CTO，run() 并行调度 ArchitectAgent/ReviewAgent/DebugAgent（均为 Haiku）
- henry.py：Henry(BaseAgent) CMO，run() 并行调度 CommunityAgent/ContentAgent/AnalyticsAgent（均为 Haiku），含行为护栏
- main.py：三种模式：交互式REPL / --task 无人值守 / --refine <dir> --feedback 迭代优化

技术栈：Python 3.10+, claude-opus-4-6（主Agent）, claude-haiku-4-5（子Agent）, asyncio, httpx, python-dotenv

要求输出6个文件，每个文件用 === FILE: 文件名 === 作为分隔符开头。
文件清单：README.md、ARCHITECTURE.md、CONTRIBUTING.md、.github/ISSUE_TEMPLATE/bug_report.yml、.github/ISSUE_TEMPLATE/feature_request.yml、LAUNCH_PLAN.md

---

I'll generate all 6 open-source launch deliverables now. Each file will be complete and production-ready.
