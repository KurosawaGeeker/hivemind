# Hive Mind 行动时间线
**任务**: 以下是团队上一轮的输出成果，请在保留优点的基础上，根据改进反馈重新输出全部文件。
每个文件用 === FILE: 文件名 === 作为分隔符开头，不要省略任何文件。



改进反馈：
README 缺少 stdin 管道用法说明（snaplog 应支持从 stdin 读取日志）；CONTRIBUTING 测试部分太简略，需要补充 conftest.py fixtures 使用示例；ARCHITECTURE.md 的扩展点章节可以加一个完整的自定义 Parser 示例代码

上一轮产出：

=== FILE: ARCHITECTURE.md ===
# 🏗️ snaplog 架构文档

本文档描述 snaplog 的内部架构，帮助贡献者快速理解代码组织和数据流。

---

## 目录结构

```
snaplog/
├── __init__.py          # 版本号、包元数据
├── cli.py               # Click 命令定义（入口）
├── parser.py            # 日志行解析引擎
├── filters.py           # 过滤器（级别、时间、正则）
├── stats.py             # 统计聚合逻辑
├── exporters.py         # JSON / CSV 导出器
├── formatters.py        # Rich 终端输出格式化
├── models.py            # 数据模型（LogEntry dataclass）
└── utils.py             # 时间解析、文件探测等工具函数
tests/
├── conftest.py          # pytest fixtures
├── test_parser.py
├── test_filters.py
├── test_stats.py
├── test_exporters.py
└── test_cli.py
pyproject.toml           # 构建配置（PEP 621）
```

---

## 核心数据模型

```python
@dataclass(frozen=True, slots=True)
class LogEntry:
    timestamp: datetime | None
    level: str            # DEBUG / INFO / WARNING / ERROR / CRITICAL
    message: str
    raw: str              # 原始行文本
    line_number: int
```

所有模块围绕 `LogEntry` 进行流转，保持单一数据契约。

---

## 数据流

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌────────────┐
│  文件/   │────▶│  Parser  │────▶│ Filters  │────▶│ Formatter  │
│  stdin   │     │          │     │          │     │ / Exporter  │
└──────────┘     └──────────┘     └──────────┘     └────────────┘
                      │                                   │
                      │           ┌──────────┐            │
                      └──────────▶│  Stats   │────────────┘
                                  └──────────┘
```

1. **输入层** — `cli.py` 接收文件路径或 stdin，逐行读取。
2. **解析层** — `parser.py` 将原始文本行转为 `LogEntry`。支持多种格式自动探测，也可通过 `--pattern` 指定。
3. **过滤层** — `filters.py` 提供可组合的过滤器链（级别、时间范围）。过滤器实现为生成器，支持惰性求值，内存占用恒定。
4. **聚合层** — `stats.py` 对过滤后的条目做单遍扫描统计（计数、Top-N 等）。
5. **输出层** — `formatters.py`（Rich 表格输出到终端）或 `exporters.py`（JSON/CSV 写入文件）。

---

## 设计原则

| 原则 | 实践 |
|------|------|
| 流式处理 | 全链路使用 Python 生成器，处理 GB 级日志不爆内存 |
| 零外部依赖 | 运行时仅依赖 Click + Rich，均为纯 Python 包 |
| 可组合 | 每个过滤器/导出器独立，可自由组合 |
| 可测试 | 核心逻辑与 CLI 层解耦，纯函数优先 |
| 类型安全 | 全面使用 Python 3.10+ 类型标注，配合 mypy strict 模式 |

---

## CLI 层设计

使用 Click 的 `@group` + `@command` 模式：

```python
@click.group()
@click.option("--no-color", is_flag=True)
@click.pass_context
def cli(ctx, no_color): ...

@cli.command()
@click.option("--level", multiple=True)
@click.argument("logfile", type=click.Path(exists=True))
def filter(level, logfile): ...

@cli.command()
@click.option("--from", "--to", ...)
def slice(...): ...

@cli.command()
def stats(...): ...

@cli.command()
@click.option("--format", type=click.Choice(["json", "csv"]))
@click.option("--output", type=click.Path())
def export(...): ...
```

---

## 解析器架构

`parser.py` 采用策略模式：

```python
class ParserStrategy(Protocol):
    def parse(self, line: str, line_number: int) -> LogEntry | None: ...

class StandardParser:    ...   # "2026-02-24 10:03:12 ERROR msg"
class SyslogParser:      ...   # "Feb 24 10:03:12 host app[pid]: ERROR msg"
class CustomParser:      ...   # 用户自定义 pattern

def auto_detect(sample_lines: list[str]) -> ParserStrategy:
    """取前 10 行，逐一尝试各策略，返回匹配率最高的。"""
```

---

## 扩展点

- 新增日志格式：实现 `ParserStrategy` 协议即可。
- 新增导出格式：在 `exporters.py` 中添加导出函数，注册到 `--format` 的 `Choice` 列表。
- 新增过滤器：在 `filters.py` 中编写生成器函数，插入过滤链。


=== FILE: CONTRIBUTING.md ===
# 🤝 贡献指南

感谢你对 snaplog 的关注！无论是修复 typo 还是添加新功能，我们都非常欢迎。

---

## 快速开始

```bash
# 1. Fork 并克隆
git clone https://github.com/<your-username>/snaplog.git
cd snaplog

# 2. 创建虚拟环境
python3.10 -m venv .venv
source .venv/bin/activate

# 3. 安装开发依赖
pip install -e ".[dev]"

# 4. 确认测试通过
pytest
```

---

## 开发工作流

1. 从 `main` 创建功能分支：`git checkout -b feat/your-feature`
2. 编写代码 + 测试
3. 本地检查：
   ```bash
   pytest                # 单元测试
   mypy snaplog          # 类型检查
   ruff check snaplog    # 代码风格
   ruff format snaplog   # 自动格式化
   ```
4. 提交（遵循 Conventional Commits）：
   ```
   feat: add regex filter support
   fix: handle empty timestamp gracefully
   docs: update CLI usage examples
   ```
5. 推送并创建 Pull Request

---

## PR 规范

- 标题使用 Conventional Commits 格式
- 描述中说明「做了什么」和「为什么」
- 关联相关 Issue（`Closes #123`）
- 确保 CI 全绿（测试 + 类型检查 + lint）
- 新功能需附带测试，覆盖率不低于现有水平

---

## 代码风格

- 格式化：[Ruff](https://docs.astral.sh/ruff/)（行宽 88）
- 类型标注：所有公开函数必须有完整类型签名
- 文档字符串：Google 风格
- 命名：`snake_case`（函数/变量），`PascalCase`（类）

---

## 测试

```bash
# 运行全部测试
pytest

# 带覆盖率
pytest --cov=snaplog --cov-report=term-missing

# 只跑某个模块
pytest tests/test_parser.py -v
```

测试文件放在 `tests/` 目录，命名 `test_<module>.py`。使用 `conftest.py` 中的 fixtures 获取示例日志数据。

---

## Issue 与讨论

- Bug 报告：使用 [Bug Report 模板](.github/ISSUE_TEMPLATE/bug_report.yml)
- 功能建议：使用 [Feature Request 模板](.github/ISSUE_TEMPLATE/feature_request.yml)
- 一般讨论：在 GitHub Discussions 中发帖

---

## 行为准则

本项目遵循 [Contributor Covenant 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)。参与即表示你同意遵守该准则。

---

## 许可

你提交的所有贡献将按 MIT 许可证授权。


=== FILE: LAUNCH_PLAN.md ===
# 🚀 snaplog 开源发布计划

## 发布目标

将 snaplog 作为高质量 Python CLI 工具开源发布，建立初始社区，在发布后 30 天内达到 500 GitHub stars。

---

## 阶段一：发布准备（D-7 → D-Day）

| 事项 | 负责 | 状态 |
|------|------|------|
| 代码审查 & 清理（移除内部引用、硬编码路径） | Tech | ⬜ |
| 测试覆盖率 ≥ 90% | Tech | ⬜ |
| mypy strict + ruff 零警告 | Tech | ⬜ |
| pyproject.toml 元数据完善 | Tech | ⬜ |
| README / ARCHITECTURE / CONTRIBUTING 定稿 | PM | ⬜ |
| LICENSE (MIT) 文件 | PM | ⬜ |
| GitHub repo 设置（Topics、About、Social Preview） | PM | ⬜ |
| Issue 模板 & PR 模板 | PM | ⬜ |
| GitHub Actions CI（测试 + lint + 发布） | Tech | ⬜ |
| PyPI 账号 & trusted publisher 配置 | Tech | ⬜ |

---

## 阶段二：发布日（D-Day）

### 技术发布

1. 打 tag `v0.1.0`，触发 CI 自动发布到 PyPI
2. 确认 `pip install snaplog` 可用
3. 创建 GitHub Release，附 changelog

### 社区传播

| 渠道 | 内容策略 | 时间 |
|------|----------|------|
| Hacker News | "Show HN: snaplog – a fast CLI log analyzer in Python" | D-Day 上午 |
| Reddit r/Python | 功能演示 + GIF 动图 | D-Day 上午 |
| Reddit r/commandline | 侧重 CLI 体验和管道组合 | D-Day 下午 |
| Twitter/X | 30 秒演示视频 + 功能亮点线程 | D-Day |
| V2EX / 掘金 | 中文技术博文「用一条命令分析日志」 | D-Day |
| Dev.to | 英文教程 "Analyze logs like a pro with snaplog" | D+1 |

### 传播素材清单

- [ ] 终端录屏 GIF（[asciinema](https://asciinema.org/) 或 [VHS](https://github.com/charmbracelet/vhs)）
- [ ] 30 秒演示视频（MP4）
- [ ] 社交媒体配图（1200×630）
- [ ] 中文博文草稿
- [ ] 英文博文草稿

---

## 阶段三：发布后运营（D+1 → D+30）

### 第一周

- 每日检查 Issues，24 小时内首次回复
- 收集用户反馈，标记 `good first issue` 吸引贡献者
- 根据反馈发布 `v0.1.1` 热修复（如有必要）

### 第二周

- 发布「一周回顾」博文（数据：stars、downloads、issues、PRs）
- 在 Awesome Python / Awesome CLI 提交收录 PR
- 联系 2-3 位 Python 领域 KOL 试用

### 第三 & 四周

- 根据高票 Feature Request 规划 `v0.2.0`
- 建立 GitHub Discussions 或 Discord 社区频道
- 发布 `v0.2.0`（预计新增：正则过滤、多文件合并）

---

## 关键指标（D+30）

| 指标 | 目标 |
|------|------|
| GitHub Stars | 500+ |
| PyPI 周下载量 | 1,000+ |
| 已关闭 Issues | ≥ 70% |
| 外部贡献者 PR | ≥ 5 |
| 测试覆盖率 | ≥ 90% |

---

## 风险与应对

| 风险 | 应对 |
|------|------|
| 发布日无人关注 | 准备 B 计划：次日在不同时区重新发布到 HN |
| 大量 Issue 涌入 | 预设 label 体系 + 自动分类 bot |
| PyPI 发布失败 | 提前在 TestPyPI 验证完整流程 |
| 负面反馈（功能不足） | 路线图透明化，引导用户参与共建 |

---

*最后更新：2026-02-24*


=== FILE: README.md ===
<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/CLI-Click%20%2B%20Rich-orange" alt="Click + Rich">
</p>

# 📜 snaplog

**快如闪电的 CLI 日志分析工具。** 过滤、截取、统计、导出——一条命令搞定。

```
$ snaplog filter --level ERROR server.log
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Timestamp           ┃ Level ┃ Message                                ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 2026-02-24 10:03:12 │ ERROR │ Connection refused: db-primary:5432    │
│ 2026-02-24 10:05:44 │ ERROR │ Timeout waiting for response (30s)     │
└─────────────────────┴───────┴────────────────────────────────────────┘
```

---

## ✨ 功能一览

| 功能 | 命令 | 说明 |
|------|------|------|
| 按级别过滤 | `snaplog filter` | 支持 DEBUG / INFO / WARNING / ERROR / CRITICAL |
| 时间截取 | `snaplog slice` | 按起止时间截取日志片段 |
| 统计摘要 | `snaplog stats` | 各级别计数、时间跨度、高频消息 Top-N |
| 导出 | `snaplog export` | 导出为 JSON 或 CSV 格式 |

---

## 🚀 安装

```bash
pip install snaplog
```

或从源码安装：

```bash
git clone https://github.com/snaplog/snaplog.git
cd snaplog
pip install -e .
```

### 依赖

仅依赖 Python 标准库 + 两个轻量包（安装时自动拉取）：

- [Click](https://click.palletsprojects.com/) — CLI 框架
- [Rich](https://rich.readthedocs.io/) — 终端美化输出

无其他外部依赖。Python 3.10+ 即可运行。

---

## 📖 使用指南

### 按级别过滤

```bash
# 只看 ERROR 及以上
snaplog filter --level ERROR app.log

# 多级别
snaplog filter --level WARNING --level ERROR app.log
```

### 时间截取

```bash
# 截取某个时间窗口
snaplog slice --from "2026-02-24 09:00:00" --to "2026-02-24 12:00:00" app.log
```

### 统计摘要

```bash
snaplog stats app.log
```

输出示例：

```
Log Summary
───────────────────────────
Total lines   : 14,328
Time span     : 2026-02-23 00:00:01 → 2026-02-24 17:58:59
───────────────────────────
DEBUG         :  4,102  (28.6%)
INFO          :  8,541  (59.6%)
WARNING       :  1,203  ( 8.4%)
ERROR         :    412  ( 2.9%)
CRITICAL      :     70  ( 0.5%)
───────────────────────────
Top-5 Messages:
 1. "Connection reset by peer"          × 87
 2. "Retry attempt exceeded"            × 63
 ...
```

### 导出

```bash
# 导出为 JSON
snaplog export --format json --output result.json app.log

# 导出为 CSV
snaplog export --format csv --output result.csv app.log

# 可与 filter/slice 组合
snaplog filter --level ERROR app.log | snaplog export --format json --output errors.json -
```

### 全局选项

```bash
snaplog --help          # 查看所有命令
snaplog filter --help   # 查看子命令帮助
snaplog --no-color ...  # 禁用彩色输出（适合管道）
```

---

## 📐 日志格式支持

snaplog 自动识别以下常见格式：

```
# 标准格式
2026-02-24 10:03:12 ERROR Connection refused
# syslog 风格
Feb 24 10:03:12 hostname app[1234]: ERROR Connection refused
# 自定义分隔符（通过 --pattern 指定）
snaplog filter --pattern "{timestamp}|{level}|{message}" --level ERROR app.log
```

---

## 🗺️ 路线图

- [x] 按级别过滤
- [x] 时间截取
- [x] 统计摘要
- [x] JSON / CSV 导出
- [ ] 正则表达式过滤 (`--grep`)
- [ ] 多文件合并分析
- [ ] 实时尾部跟踪 (`snaplog tail`)
- [ ] 插件系统（自定义解析器）

---

## 🤝 参与贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解流程。

---

## 📄 许可证

[MIT License](LICENSE) © 2026 snaplog contributors


=== FILE: .github/ISSUE_TEMPLATE/bug_report.yml ===
```yaml
name: 🐛 Bug 报告
description: 报告 snaplog 的问题或异常行为
title: "[Bug]: "
labels: ["bug", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        感谢你花时间报告问题！请尽量填写以下信息，帮助我们快速定位。

  - type: input
    id: version
    attributes:
      label: snaplog 版本
      description: "运行 `snaplog --version` 获取"
      placeholder: "0.1.0"
    validations:
      required: true

  - type: input
    id: python-version
    attributes:
      label: Python 版本
      description: "运行 `python --version` 获取"
      placeholder: "3.10.12"
    validations:
      required: true

  - type: dropdown
    id: os
    attributes:
      label: 操作系统
      options:
        - macOS
        - Linux
        - Windows
        - 其他
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: 问题描述
      description: 清晰简洁地描述遇到的问题
    validations:
      required: true

  - type: textarea
    id: reproduce
    attributes:
      label: 复现步骤
      description: 提供最小复现步骤
      value: |
        1. 准备日志文件（内容示例）：
           ```
           2026-02-24 10:00:00 ERROR something broke
           ```
        2. 运行命令：
           ```bash
           snaplog filter --level ERROR test.log
           ```
        3. 观察到的行为：...
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: 期望行为
      description: 你期望发生什么？
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: 错误输出 / 堆栈信息
      description: 粘贴完整的终端输出
      render: shell

  - type: textarea
    id: additional
    attributes:
      label: 补充信息
      description: 任何有助于排查的额外上下文（截图、日志文件片段等）
```


=== FILE: .github/ISSUE_TEMPLATE/feature_request.yml ===
```yaml
name: ✨ 功能建议
description: 提出新功能或改进建议
title: "[Feature]: "
labels: ["enhancement"]
body:
  - type: markdown
    attributes:
      value: |
        感谢你的建议！好的想法让 snaplog 变得更好。

  - type: textarea
    id: problem
    attributes:
      label: 问题或动机
      description: 你想解决什么问题？或者在什么场景下需要这个功能？
      placeholder: "当我分析多个日志文件时，需要手动合并，非常繁琐..."
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: 期望的解决方案
      description: 描述你理想中的功能表现
      placeholder: |
        希望支持多文件输入：
        ```bash
        snaplog stats app1.log app2.log app3.log
        ```
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: 替代方案
      description: 你考虑过哪些替代方案？

  - type: dropdown
    id: scope
    attributes:
      label: 影响范围
      options:
        - 新命令
        - 现有命令增强
        - 输出格式
        - 性能优化
        - 文档改进
        - 其他
    validations:
      required: true

  - type: checkboxes
    id: contribution
    attributes:
      label: 参与意愿
      options:
        - label: 我愿意提交 PR 来实现这个功能
```

**时间**: 2026-02-25 02:30:41

| 耗时(s) | Agent | 事件 | 备注 |
|---------|-------|------|------|
| +0.01 | Echo | Coordinating strategic input: 以下是团队上一轮的输出成果，请在保留优点的基础上，根据改进反馈重新输出全部文件。
每个文件用 === FILE: 文件名 === 作为分隔符开头，不要省略任何文件。



改进反馈：
README 缺少 stdin 管道用法说明（snaplog 应支持从 stdin 读取日志）；CONTRIBUTING 测试部分太简略，需要补充 conftest.py fixtures 使用示例；ARCHITECTURE.md 的扩展点章节可以加一个完整的自定义 Parser 示例代码

上一轮产出：

=== FILE: ARCHITECTURE.md ===
# 🏗️ snaplog 架构文档

本文档描述 snaplog 的内部架构，帮助贡献者快速理解代码组织和数据流。

---

## 目录结构

```
snaplog/
├── __init__.py          # 版本号、包元数据
├── cli.py               # Click 命令定义（入口）
├── parser.py            # 日志行解析引擎
├── filters.py           # 过滤器（级别、时间、正则）
├── stats.py             # 统计聚合逻辑
├── exporters.py         # JSON / CSV 导出器
├── formatters.py        # Rich 终端输出格式化
├── models.py            # 数据模型（LogEntry dataclass）
└── utils.py             # 时间解析、文件探测等工具函数
tests/
├── conftest.py          # pytest fixtures
├── test_parser.py
├── test_filters.py
├── test_stats.py
├── test_exporters.py
└── test_cli.py
pyproject.toml           # 构建配置（PEP 621）
```

---

## 核心数据模型

```python
@dataclass(frozen=True, slots=True)
class LogEntry:
    timestamp: datetime | None
    level: str            # DEBUG / INFO / WARNING / ERROR / CRITICAL
    message: str
    raw: str              # 原始行文本
    line_number: int
```

所有模块围绕 `LogEntry` 进行流转，保持单一数据契约。

---

## 数据流

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌────────────┐
│  文件/   │────▶│  Parser  │────▶│ Filters  │────▶│ Formatter  │
│  stdin   │     │          │     │          │     │ / Exporter  │
└──────────┘     └──────────┘     └──────────┘     └────────────┘
                      │                                   │
                      │           ┌──────────┐            │
                      └──────────▶│  Stats   │────────────┘
                                  └──────────┘
```

1. **输入层** — `cli.py` 接收文件路径或 stdin，逐行读取。
2. **解析层** — `parser.py` 将原始文本行转为 `LogEntry`。支持多种格式自动探测，也可通过 `--pattern` 指定。
3. **过滤层** — `filters.py` 提供可组合的过滤器链（级别、时间范围）。过滤器实现为生成器，支持惰性求值，内存占用恒定。
4. **聚合层** — `stats.py` 对过滤后的条目做单遍扫描统计（计数、Top-N 等）。
5. **输出层** — `formatters.py`（Rich 表格输出到终端）或 `exporters.py`（JSON/CSV 写入文件）。

---

## 设计原则

| 原则 | 实践 |
|------|------|
| 流式处理 | 全链路使用 Python 生成器，处理 GB 级日志不爆内存 |
| 零外部依赖 | 运行时仅依赖 Click + Rich，均为纯 Python 包 |
| 可组合 | 每个过滤器/导出器独立，可自由组合 |
| 可测试 | 核心逻辑与 CLI 层解耦，纯函数优先 |
| 类型安全 | 全面使用 Python 3.10+ 类型标注，配合 mypy strict 模式 |

---

## CLI 层设计

使用 Click 的 `@group` + `@command` 模式：

```python
@click.group()
@click.option("--no-color", is_flag=True)
@click.pass_context
def cli(ctx, no_color): ...

@cli.command()
@click.option("--level", multiple=True)
@click.argument("logfile", type=click.Path(exists=True))
def filter(level, logfile): ...

@cli.command()
@click.option("--from", "--to", ...)
def slice(...): ...

@cli.command()
def stats(...): ...

@cli.command()
@click.option("--format", type=click.Choice(["json", "csv"]))
@click.option("--output", type=click.Path())
def export(...): ...
```

---

## 解析器架构

`parser.py` 采用策略模式：

```python
class ParserStrategy(Protocol):
    def parse(self, line: str, line_number: int) -> LogEntry | None: ...

class StandardParser:    ...   # "2026-02-24 10:03:12 ERROR msg"
class SyslogParser:      ...   # "Feb 24 10:03:12 host app[pid]: ERROR msg"
class CustomParser:      ...   # 用户自定义 pattern

def auto_detect(sample_lines: list[str]) -> ParserStrategy:
    """取前 10 行，逐一尝试各策略，返回匹配率最高的。"""
```

---

## 扩展点

- 新增日志格式：实现 `ParserStrategy` 协议即可。
- 新增导出格式：在 `exporters.py` 中添加导出函数，注册到 `--format` 的 `Choice` 列表。
- 新增过滤器：在 `filters.py` 中编写生成器函数，插入过滤链。


=== FILE: CONTRIBUTING.md ===
# 🤝 贡献指南

感谢你对 snaplog 的关注！无论是修复 typo 还是添加新功能，我们都非常欢迎。

---

## 快速开始

```bash
# 1. Fork 并克隆
git clone https://github.com/<your-username>/snaplog.git
cd snaplog

# 2. 创建虚拟环境
python3.10 -m venv .venv
source .venv/bin/activate

# 3. 安装开发依赖
pip install -e ".[dev]"

# 4. 确认测试通过
pytest
```

---

## 开发工作流

1. 从 `main` 创建功能分支：`git checkout -b feat/your-feature`
2. 编写代码 + 测试
3. 本地检查：
   ```bash
   pytest                # 单元测试
   mypy snaplog          # 类型检查
   ruff check snaplog    # 代码风格
   ruff format snaplog   # 自动格式化
   ```
4. 提交（遵循 Conventional Commits）：
   ```
   feat: add regex filter support
   fix: handle empty timestamp gracefully
   docs: update CLI usage examples
   ```
5. 推送并创建 Pull Request

---

## PR 规范

- 标题使用 Conventional Commits 格式
- 描述中说明「做了什么」和「为什么」
- 关联相关 Issue（`Closes #123`）
- 确保 CI 全绿（测试 + 类型检查 + lint）
- 新功能需附带测试，覆盖率不低于现有水平

---

## 代码风格

- 格式化：[Ruff](https://docs.astral.sh/ruff/)（行宽 88）
- 类型标注：所有公开函数必须有完整类型签名
- 文档字符串：Google 风格
- 命名：`snake_case`（函数/变量），`PascalCase`（类）

---

## 测试

```bash
# 运行全部测试
pytest

# 带覆盖率
pytest --cov=snaplog --cov-report=term-missing

# 只跑某个模块
pytest tests/test_parser.py -v
```

测试文件放在 `tests/` 目录，命名 `test_<module>.py`。使用 `conftest.py` 中的 fixtures 获取示例日志数据。

---

## Issue 与讨论

- Bug 报告：使用 [Bug Report 模板](.github/ISSUE_TEMPLATE/bug_report.yml)
- 功能建议：使用 [Feature Request 模板](.github/ISSUE_TEMPLATE/feature_request.yml)
- 一般讨论：在 GitHub Discussions 中发帖

---

## 行为准则

本项目遵循 [Contributor Covenant 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)。参与即表示你同意遵守该准则。

---

## 许可

你提交的所有贡献将按 MIT 许可证授权。


=== FILE: LAUNCH_PLAN.md ===
# 🚀 snaplog 开源发布计划

## 发布目标

将 snaplog 作为高质量 Python CLI 工具开源发布，建立初始社区，在发布后 30 天内达到 500 GitHub stars。

---

## 阶段一：发布准备（D-7 → D-Day）

| 事项 | 负责 | 状态 |
|------|------|------|
| 代码审查 & 清理（移除内部引用、硬编码路径） | Tech | ⬜ |
| 测试覆盖率 ≥ 90% | Tech | ⬜ |
| mypy strict + ruff 零警告 | Tech | ⬜ |
| pyproject.toml 元数据完善 | Tech | ⬜ |
| README / ARCHITECTURE / CONTRIBUTING 定稿 | PM | ⬜ |
| LICENSE (MIT) 文件 | PM | ⬜ |
| GitHub repo 设置（Topics、About、Social Preview） | PM | ⬜ |
| Issue 模板 & PR 模板 | PM | ⬜ |
| GitHub Actions CI（测试 + lint + 发布） | Tech | ⬜ |
| PyPI 账号 & trusted publisher 配置 | Tech | ⬜ |

---

## 阶段二：发布日（D-Day）

### 技术发布

1. 打 tag `v0.1.0`，触发 CI 自动发布到 PyPI
2. 确认 `pip install snaplog` 可用
3. 创建 GitHub Release，附 changelog

### 社区传播

| 渠道 | 内容策略 | 时间 |
|------|----------|------|
| Hacker News | "Show HN: snaplog – a fast CLI log analyzer in Python" | D-Day 上午 |
| Reddit r/Python | 功能演示 + GIF 动图 | D-Day 上午 |
| Reddit r/commandline | 侧重 CLI 体验和管道组合 | D-Day 下午 |
| Twitter/X | 30 秒演示视频 + 功能亮点线程 | D-Day |
| V2EX / 掘金 | 中文技术博文「用一条命令分析日志」 | D-Day |
| Dev.to | 英文教程 "Analyze logs like a pro with snaplog" | D+1 |

### 传播素材清单

- [ ] 终端录屏 GIF（[asciinema](https://asciinema.org/) 或 [VHS](https://github.com/charmbracelet/vhs)）
- [ ] 30 秒演示视频（MP4）
- [ ] 社交媒体配图（1200×630）
- [ ] 中文博文草稿
- [ ] 英文博文草稿

---

## 阶段三：发布后运营（D+1 → D+30）

### 第一周

- 每日检查 Issues，24 小时内首次回复
- 收集用户反馈，标记 `good first issue` 吸引贡献者
- 根据反馈发布 `v0.1.1` 热修复（如有必要）

### 第二周

- 发布「一周回顾」博文（数据：stars、downloads、issues、PRs）
- 在 Awesome Python / Awesome CLI 提交收录 PR
- 联系 2-3 位 Python 领域 KOL 试用

### 第三 & 四周

- 根据高票 Feature Request 规划 `v0.2.0`
- 建立 GitHub Discussions 或 Discord 社区频道
- 发布 `v0.2.0`（预计新增：正则过滤、多文件合并）

---

## 关键指标（D+30）

| 指标 | 目标 |
|------|------|
| GitHub Stars | 500+ |
| PyPI 周下载量 | 1,000+ |
| 已关闭 Issues | ≥ 70% |
| 外部贡献者 PR | ≥ 5 |
| 测试覆盖率 | ≥ 90% |

---

## 风险与应对

| 风险 | 应对 |
|------|------|
| 发布日无人关注 | 准备 B 计划：次日在不同时区重新发布到 HN |
| 大量 Issue 涌入 | 预设 label 体系 + 自动分类 bot |
| PyPI 发布失败 | 提前在 TestPyPI 验证完整流程 |
| 负面反馈（功能不足） | 路线图透明化，引导用户参与共建 |

---

*最后更新：2026-02-24*


=== FILE: README.md ===
<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/CLI-Click%20%2B%20Rich-orange" alt="Click + Rich">
</p>

# 📜 snaplog

**快如闪电的 CLI 日志分析工具。** 过滤、截取、统计、导出——一条命令搞定。

```
$ snaplog filter --level ERROR server.log
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Timestamp           ┃ Level ┃ Message                                ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 2026-02-24 10:03:12 │ ERROR │ Connection refused: db-primary:5432    │
│ 2026-02-24 10:05:44 │ ERROR │ Timeout waiting for response (30s)     │
└─────────────────────┴───────┴────────────────────────────────────────┘
```

---

## ✨ 功能一览

| 功能 | 命令 | 说明 |
|------|------|------|
| 按级别过滤 | `snaplog filter` | 支持 DEBUG / INFO / WARNING / ERROR / CRITICAL |
| 时间截取 | `snaplog slice` | 按起止时间截取日志片段 |
| 统计摘要 | `snaplog stats` | 各级别计数、时间跨度、高频消息 Top-N |
| 导出 | `snaplog export` | 导出为 JSON 或 CSV 格式 |

---

## 🚀 安装

```bash
pip install snaplog
```

或从源码安装：

```bash
git clone https://github.com/snaplog/snaplog.git
cd snaplog
pip install -e .
```

### 依赖

仅依赖 Python 标准库 + 两个轻量包（安装时自动拉取）：

- [Click](https://click.palletsprojects.com/) — CLI 框架
- [Rich](https://rich.readthedocs.io/) — 终端美化输出

无其他外部依赖。Python 3.10+ 即可运行。

---

## 📖 使用指南

### 按级别过滤

```bash
# 只看 ERROR 及以上
snaplog filter --level ERROR app.log

# 多级别
snaplog filter --level WARNING --level ERROR app.log
```

### 时间截取

```bash
# 截取某个时间窗口
snaplog slice --from "2026-02-24 09:00:00" --to "2026-02-24 12:00:00" app.log
```

### 统计摘要

```bash
snaplog stats app.log
```

输出示例：

```
Log Summary
───────────────────────────
Total lines   : 14,328
Time span     : 2026-02-23 00:00:01 → 2026-02-24 17:58:59
───────────────────────────
DEBUG         :  4,102  (28.6%)
INFO          :  8,541  (59.6%)
WARNING       :  1,203  ( 8.4%)
ERROR         :    412  ( 2.9%)
CRITICAL      :     70  ( 0.5%)
───────────────────────────
Top-5 Messages:
 1. "Connection reset by peer"          × 87
 2. "Retry attempt exceeded"            × 63
 ...
```

### 导出

```bash
# 导出为 JSON
snaplog export --format json --output result.json app.log

# 导出为 CSV
snaplog export --format csv --output result.csv app.log

# 可与 filter/slice 组合
snaplog filter --level ERROR app.log | snaplog export --format json --output errors.json -
```

### 全局选项

```bash
snaplog --help          # 查看所有命令
snaplog filter --help   # 查看子命令帮助
snaplog --no-color ...  # 禁用彩色输出（适合管道）
```

---

## 📐 日志格式支持

snaplog 自动识别以下常见格式：

```
# 标准格式
2026-02-24 10:03:12 ERROR Connection refused
# syslog 风格
Feb 24 10:03:12 hostname app[1234]: ERROR Connection refused
# 自定义分隔符（通过 --pattern 指定）
snaplog filter --pattern "{timestamp}|{level}|{message}" --level ERROR app.log
```

---

## 🗺️ 路线图

- [x] 按级别过滤
- [x] 时间截取
- [x] 统计摘要
- [x] JSON / CSV 导出
- [ ] 正则表达式过滤 (`--grep`)
- [ ] 多文件合并分析
- [ ] 实时尾部跟踪 (`snaplog tail`)
- [ ] 插件系统（自定义解析器）

---

## 🤝 参与贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解流程。

---

## 📄 许可证

[MIT License](LICENSE) © 2026 snaplog contributors


=== FILE: .github/ISSUE_TEMPLATE/bug_report.yml ===
```yaml
name: 🐛 Bug 报告
description: 报告 snaplog 的问题或异常行为
title: "[Bug]: "
labels: ["bug", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        感谢你花时间报告问题！请尽量填写以下信息，帮助我们快速定位。

  - type: input
    id: version
    attributes:
      label: snaplog 版本
      description: "运行 `snaplog --version` 获取"
      placeholder: "0.1.0"
    validations:
      required: true

  - type: input
    id: python-version
    attributes:
      label: Python 版本
      description: "运行 `python --version` 获取"
      placeholder: "3.10.12"
    validations:
      required: true

  - type: dropdown
    id: os
    attributes:
      label: 操作系统
      options:
        - macOS
        - Linux
        - Windows
        - 其他
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: 问题描述
      description: 清晰简洁地描述遇到的问题
    validations:
      required: true

  - type: textarea
    id: reproduce
    attributes:
      label: 复现步骤
      description: 提供最小复现步骤
      value: |
        1. 准备日志文件（内容示例）：
           ```
           2026-02-24 10:00:00 ERROR something broke
           ```
        2. 运行命令：
           ```bash
           snaplog filter --level ERROR test.log
           ```
        3. 观察到的行为：...
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: 期望行为
      description: 你期望发生什么？
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: 错误输出 / 堆栈信息
      description: 粘贴完整的终端输出
      render: shell

  - type: textarea
    id: additional
    attributes:
      label: 补充信息
      description: 任何有助于排查的额外上下文（截图、日志文件片段等）
```


=== FILE: .github/ISSUE_TEMPLATE/feature_request.yml ===
```yaml
name: ✨ 功能建议
description: 提出新功能或改进建议
title: "[Feature]: "
labels: ["enhancement"]
body:
  - type: markdown
    attributes:
      value: |
        感谢你的建议！好的想法让 snaplog 变得更好。

  - type: textarea
    id: problem
    attributes:
      label: 问题或动机
      description: 你想解决什么问题？或者在什么场景下需要这个功能？
      placeholder: "当我分析多个日志文件时，需要手动合并，非常繁琐..."
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: 期望的解决方案
      description: 描述你理想中的功能表现
      placeholder: |
        希望支持多文件输入：
        ```bash
        snaplog stats app1.log app2.log app3.log
        ```
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: 替代方案
      description: 你考虑过哪些替代方案？

  - type: dropdown
    id: scope
    attributes:
      label: 影响范围
      options:
        - 新命令
        - 现有命令增强
        - 输出格式
        - 性能优化
        - 文档改进
        - 其他
    validations:
      required: true

  - type: checkboxes
    id: contribution
    attributes:
      label: 参与意愿
      options:
        - label: 我愿意提交 PR 来实现这个功能
```
 |  |
| +0.01 | Echo | 调用 LLM | model=claude-opus-4-6 max_tokens=4096 |
| +37.05 | Echo | LLM 响应完成 | 用时约 37.0s |
| +37.05 | Elon | Dispatching sub-agents for goal: Deliver the technical implementation plan for: 以下是团队上一轮的输出成果，请在保留优点的基础上，根据改进反馈重新输出全部文件。
每个文件用 === FILE: 文件名 === 作为分隔符开头，不要省略任何文件。



改进反馈：
README 缺少 stdin 管道用法说明（snaplog 应支持从 stdin 读取日志）；CONTRIBUTING 测试部分太简略，需要补充 conftest.py fixtures 使用示例；ARCHITECTURE.md 的扩展点章节可以加一个完整的自定义 Parser 示例代码

上一轮产出：

=== FILE: ARCHITECTURE.md ===
# 🏗️ snaplog 架构文档

本文档描述 snaplog 的内部架构，帮助贡献者快速理解代码组织和数据流。

---

## 目录结构

```
snaplog/
├── __init__.py          # 版本号、包元数据
├── cli.py               # Click 命令定义（入口）
├── parser.py            # 日志行解析引擎
├── filters.py           # 过滤器（级别、时间、正则）
├── stats.py             # 统计聚合逻辑
├── exporters.py         # JSON / CSV 导出器
├── formatters.py        # Rich 终端输出格式化
├── models.py            # 数据模型（LogEntry dataclass）
└── utils.py             # 时间解析、文件探测等工具函数
tests/
├── conftest.py          # pytest fixtures
├── test_parser.py
├── test_filters.py
├── test_stats.py
├── test_exporters.py
└── test_cli.py
pyproject.toml           # 构建配置（PEP 621）
```

---

## 核心数据模型

```python
@dataclass(frozen=True, slots=True)
class LogEntry:
    timestamp: datetime | None
    level: str            # DEBUG / INFO / WARNING / ERROR / CRITICAL
    message: str
    raw: str              # 原始行文本
    line_number: int
```

所有模块围绕 `LogEntry` 进行流转，保持单一数据契约。

---

## 数据流

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌────────────┐
│  文件/   │────▶│  Parser  │────▶│ Filters  │────▶│ Formatter  │
│  stdin   │     │          │     │          │     │ / Exporter  │
└──────────┘     └──────────┘     └──────────┘     └────────────┘
                      │                                   │
                      │           ┌──────────┐            │
                      └──────────▶│  Stats   │────────────┘
                                  └──────────┘
```

1. **输入层** — `cli.py` 接收文件路径或 stdin，逐行读取。
2. **解析层** — `parser.py` 将原始文本行转为 `LogEntry`。支持多种格式自动探测，也可通过 `--pattern` 指定。
3. **过滤层** — `filters.py` 提供可组合的过滤器链（级别、时间范围）。过滤器实现为生成器，支持惰性求值，内存占用恒定。
4. **聚合层** — `stats.py` 对过滤后的条目做单遍扫描统计（计数、Top-N 等）。
5. **输出层** — `formatters.py`（Rich 表格输出到终端）或 `exporters.py`（JSON/CSV 写入文件）。

---

## 设计原则

| 原则 | 实践 |
|------|------|
| 流式处理 | 全链路使用 Python 生成器，处理 GB 级日志不爆内存 |
| 零外部依赖 | 运行时仅依赖 Click + Rich，均为纯 Python 包 |
| 可组合 | 每个过滤器/导出器独立，可自由组合 |
| 可测试 | 核心逻辑与 CLI 层解耦，纯函数优先 |
| 类型安全 | 全面使用 Python 3.10+ 类型标注，配合 mypy strict 模式 |

---

## CLI 层设计

使用 Click 的 `@group` + `@command` 模式：

```python
@click.group()
@click.option("--no-color", is_flag=True)
@click.pass_context
def cli(ctx, no_color): ...

@cli.command()
@click.option("--level", multiple=True)
@click.argument("logfile", type=click.Path(exists=True))
def filter(level, logfile): ...

@cli.command()
@click.option("--from", "--to", ...)
def slice(...): ...

@cli.command()
def stats(...): ...

@cli.command()
@click.option("--format", type=click.Choice(["json", "csv"]))
@click.option("--output", type=click.Path())
def export(...): ...
```

---

## 解析器架构

`parser.py` 采用策略模式：

```python
class ParserStrategy(Protocol):
    def parse(self, line: str, line_number: int) -> LogEntry | None: ...

class StandardParser:    ...   # "2026-02-24 10:03:12 ERROR msg"
class SyslogParser:      ...   # "Feb 24 10:03:12 host app[pid]: ERROR msg"
class CustomParser:      ...   # 用户自定义 pattern

def auto_detect(sample_lines: list[str]) -> ParserStrategy:
    """取前 10 行，逐一尝试各策略，返回匹配率最高的。"""
```

---

## 扩展点

- 新增日志格式：实现 `ParserStrategy` 协议即可。
- 新增导出格式：在 `exporters.py` 中添加导出函数，注册到 `--format` 的 `Choice` 列表。
- 新增过滤器：在 `filters.py` 中编写生成器函数，插入过滤链。


=== FILE: CONTRIBUTING.md ===
# 🤝 贡献指南

感谢你对 snaplog 的关注！无论是修复 typo 还是添加新功能，我们都非常欢迎。

---

## 快速开始

```bash
# 1. Fork 并克隆
git clone https://github.com/<your-username>/snaplog.git
cd snaplog

# 2. 创建虚拟环境
python3.10 -m venv .venv
source .venv/bin/activate

# 3. 安装开发依赖
pip install -e ".[dev]"

# 4. 确认测试通过
pytest
```

---

## 开发工作流

1. 从 `main` 创建功能分支：`git checkout -b feat/your-feature`
2. 编写代码 + 测试
3. 本地检查：
   ```bash
   pytest                # 单元测试
   mypy snaplog          # 类型检查
   ruff check snaplog    # 代码风格
   ruff format snaplog   # 自动格式化
   ```
4. 提交（遵循 Conventional Commits）：
   ```
   feat: add regex filter support
   fix: handle empty timestamp gracefully
   docs: update CLI usage examples
   ```
5. 推送并创建 Pull Request

---

## PR 规范

- 标题使用 Conventional Commits 格式
- 描述中说明「做了什么」和「为什么」
- 关联相关 Issue（`Closes #123`）
- 确保 CI 全绿（测试 + 类型检查 + lint）
- 新功能需附带测试，覆盖率不低于现有水平

---

## 代码风格

- 格式化：[Ruff](https://docs.astral.sh/ruff/)（行宽 88）
- 类型标注：所有公开函数必须有完整类型签名
- 文档字符串：Google 风格
- 命名：`snake_case`（函数/变量），`PascalCase`（类）

---

## 测试

```bash
# 运行全部测试
pytest

# 带覆盖率
pytest --cov=snaplog --cov-report=term-missing

# 只跑某个模块
pytest tests/test_parser.py -v
```

测试文件放在 `tests/` 目录，命名 `test_<module>.py`。使用 `conftest.py` 中的 fixtures 获取示例日志数据。

---

## Issue 与讨论

- Bug 报告：使用 [Bug Report 模板](.github/ISSUE_TEMPLATE/bug_report.yml)
- 功能建议：使用 [Feature Request 模板](.github/ISSUE_TEMPLATE/feature_request.yml)
- 一般讨论：在 GitHub Discussions 中发帖

---

## 行为准则

本项目遵循 [Contributor Covenant 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)。参与即表示你同意遵守该准则。

---

## 许可

你提交的所有贡献将按 MIT 许可证授权。


=== FILE: LAUNCH_PLAN.md ===
# 🚀 snaplog 开源发布计划

## 发布目标

将 snaplog 作为高质量 Python CLI 工具开源发布，建立初始社区，在发布后 30 天内达到 500 GitHub stars。

---

## 阶段一：发布准备（D-7 → D-Day）

| 事项 | 负责 | 状态 |
|------|------|------|
| 代码审查 & 清理（移除内部引用、硬编码路径） | Tech | ⬜ |
| 测试覆盖率 ≥ 90% | Tech | ⬜ |
| mypy strict + ruff 零警告 | Tech | ⬜ |
| pyproject.toml 元数据完善 | Tech | ⬜ |
| README / ARCHITECTURE / CONTRIBUTING 定稿 | PM | ⬜ |
| LICENSE (MIT) 文件 | PM | ⬜ |
| GitHub repo 设置（Topics、About、Social Preview） | PM | ⬜ |
| Issue 模板 & PR 模板 | PM | ⬜ |
| GitHub Actions CI（测试 + lint + 发布） | Tech | ⬜ |
| PyPI 账号 & trusted publisher 配置 | Tech | ⬜ |

---

## 阶段二：发布日（D-Day）

### 技术发布

1. 打 tag `v0.1.0`，触发 CI 自动发布到 PyPI
2. 确认 `pip install snaplog` 可用
3. 创建 GitHub Release，附 changelog

### 社区传播

| 渠道 | 内容策略 | 时间 |
|------|----------|------|
| Hacker News | "Show HN: snaplog – a fast CLI log analyzer in Python" | D-Day 上午 |
| Reddit r/Python | 功能演示 + GIF 动图 | D-Day 上午 |
| Reddit r/commandline | 侧重 CLI 体验和管道组合 | D-Day 下午 |
| Twitter/X | 30 秒演示视频 + 功能亮点线程 | D-Day |
| V2EX / 掘金 | 中文技术博文「用一条命令分析日志」 | D-Day |
| Dev.to | 英文教程 "Analyze logs like a pro with snaplog" | D+1 |

### 传播素材清单

- [ ] 终端录屏 GIF（[asciinema](https://asciinema.org/) 或 [VHS](https://github.com/charmbracelet/vhs)）
- [ ] 30 秒演示视频（MP4）
- [ ] 社交媒体配图（1200×630）
- [ ] 中文博文草稿
- [ ] 英文博文草稿

---

## 阶段三：发布后运营（D+1 → D+30）

### 第一周

- 每日检查 Issues，24 小时内首次回复
- 收集用户反馈，标记 `good first issue` 吸引贡献者
- 根据反馈发布 `v0.1.1` 热修复（如有必要）

### 第二周

- 发布「一周回顾」博文（数据：stars、downloads、issues、PRs）
- 在 Awesome Python / Awesome CLI 提交收录 PR
- 联系 2-3 位 Python 领域 KOL 试用

### 第三 & 四周

- 根据高票 Feature Request 规划 `v0.2.0`
- 建立 GitHub Discussions 或 Discord 社区频道
- 发布 `v0.2.0`（预计新增：正则过滤、多文件合并）

---

## 关键指标（D+30）

| 指标 | 目标 |
|------|------|
| GitHub Stars | 500+ |
| PyPI 周下载量 | 1,000+ |
| 已关闭 Issues | ≥ 70% |
| 外部贡献者 PR | ≥ 5 |
| 测试覆盖率 | ≥ 90% |

---

## 风险与应对

| 风险 | 应对 |
|------|------|
| 发布日无人关注 | 准备 B 计划：次日在不同时区重新发布到 HN |
| 大量 Issue 涌入 | 预设 label 体系 + 自动分类 bot |
| PyPI 发布失败 | 提前在 TestPyPI 验证完整流程 |
| 负面反馈（功能不足） | 路线图透明化，引导用户参与共建 |

---

*最后更新：2026-02-24*


=== FILE: README.md ===
<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/CLI-Click%20%2B%20Rich-orange" alt="Click + Rich">
</p>

# 📜 snaplog

**快如闪电的 CLI 日志分析工具。** 过滤、截取、统计、导出——一条命令搞定。

```
$ snaplog filter --level ERROR server.log
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Timestamp           ┃ Level ┃ Message                                ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 2026-02-24 10:03:12 │ ERROR │ Connection refused: db-primary:5432    │
│ 2026-02-24 10:05:44 │ ERROR │ Timeout waiting for response (30s)     │
└─────────────────────┴───────┴────────────────────────────────────────┘
```

---

## ✨ 功能一览

| 功能 | 命令 | 说明 |
|------|------|------|
| 按级别过滤 | `snaplog filter` | 支持 DEBUG / INFO / WARNING / ERROR / CRITICAL |
| 时间截取 | `snaplog slice` | 按起止时间截取日志片段 |
| 统计摘要 | `snaplog stats` | 各级别计数、时间跨度、高频消息 Top-N |
| 导出 | `snaplog export` | 导出为 JSON 或 CSV 格式 |

---

## 🚀 安装

```bash
pip install snaplog
```

或从源码安装：

```bash
git clone https://github.com/snaplog/snaplog.git
cd snaplog
pip install -e .
```

### 依赖

仅依赖 Python 标准库 + 两个轻量包（安装时自动拉取）：

- [Click](https://click.palletsprojects.com/) — CLI 框架
- [Rich](https://rich.readthedocs.io/) — 终端美化输出

无其他外部依赖。Python 3.10+ 即可运行。

---

## 📖 使用指南

### 按级别过滤

```bash
# 只看 ERROR 及以上
snaplog filter --level ERROR app.log

# 多级别
snaplog filter --level WARNING --level ERROR app.log
```

### 时间截取

```bash
# 截取某个时间窗口
snaplog slice --from "2026-02-24 09:00:00" --to "2026-02-24 12:00:00" app.log
```

### 统计摘要

```bash
snaplog stats app.log
```

输出示例：

```
Log Summary
───────────────────────────
Total lines   : 14,328
Time span     : 2026-02-23 00:00:01 → 2026-02-24 17:58:59
───────────────────────────
DEBUG         :  4,102  (28.6%)
INFO          :  8,541  (59.6%)
WARNING       :  1,203  ( 8.4%)
ERROR         :    412  ( 2.9%)
CRITICAL      :     70  ( 0.5%)
───────────────────────────
Top-5 Messages:
 1. "Connection reset by peer"          × 87
 2. "Retry attempt exceeded"            × 63
 ...
```

### 导出

```bash
# 导出为 JSON
snaplog export --format json --output result.json app.log

# 导出为 CSV
snaplog export --format csv --output result.csv app.log

# 可与 filter/slice 组合
snaplog filter --level ERROR app.log | snaplog export --format json --output errors.json -
```

### 全局选项

```bash
snaplog --help          # 查看所有命令
snaplog filter --help   # 查看子命令帮助
snaplog --no-color ...  # 禁用彩色输出（适合管道）
```

---

## 📐 日志格式支持

snaplog 自动识别以下常见格式：

```
# 标准格式
2026-02-24 10:03:12 ERROR Connection refused
# syslog 风格
Feb 24 10:03:12 hostname app[1234]: ERROR Connection refused
# 自定义分隔符（通过 --pattern 指定）
snaplog filter --pattern "{timestamp}|{level}|{message}" --level ERROR app.log
```

---

## 🗺️ 路线图

- [x] 按级别过滤
- [x] 时间截取
- [x] 统计摘要
- [x] JSON / CSV 导出
- [ ] 正则表达式过滤 (`--grep`)
- [ ] 多文件合并分析
- [ ] 实时尾部跟踪 (`snaplog tail`)
- [ ] 插件系统（自定义解析器）

---

## 🤝 参与贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解流程。

---

## 📄 许可证

[MIT License](LICENSE) © 2026 snaplog contributors


=== FILE: .github/ISSUE_TEMPLATE/bug_report.yml ===
```yaml
name: 🐛 Bug 报告
description: 报告 snaplog 的问题或异常行为
title: "[Bug]: "
labels: ["bug", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        感谢你花时间报告问题！请尽量填写以下信息，帮助我们快速定位。

  - type: input
    id: version
    attributes:
      label: snaplog 版本
      description: "运行 `snaplog --version` 获取"
      placeholder: "0.1.0"
    validations:
      required: true

  - type: input
    id: python-version
    attributes:
      label: Python 版本
      description: "运行 `python --version` 获取"
      placeholder: "3.10.12"
    validations:
      required: true

  - type: dropdown
    id: os
    attributes:
      label: 操作系统
      options:
        - macOS
        - Linux
        - Windows
        - 其他
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: 问题描述
      description: 清晰简洁地描述遇到的问题
    validations:
      required: true

  - type: textarea
    id: reproduce
    attributes:
      label: 复现步骤
      description: 提供最小复现步骤
      value: |
        1. 准备日志文件（内容示例）：
           ```
           2026-02-24 10:00:00 ERROR something broke
           ```
        2. 运行命令：
           ```bash
           snaplog filter --level ERROR test.log
           ```
        3. 观察到的行为：...
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: 期望行为
      description: 你期望发生什么？
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: 错误输出 / 堆栈信息
      description: 粘贴完整的终端输出
      render: shell

  - type: textarea
    id: additional
    attributes:
      label: 补充信息
      description: 任何有助于排查的额外上下文（截图、日志文件片段等）
```


=== FILE: .github/ISSUE_TEMPLATE/feature_request.yml ===
```yaml
name: ✨ 功能建议
description: 提出新功能或改进建议
title: "[Feature]: "
labels: ["enhancement"]
body:
  - type: markdown
    attributes:
      value: |
        感谢你的建议！好的想法让 snaplog 变得更好。

  - type: textarea
    id: problem
    attributes:
      label: 问题或动机
      description: 你想解决什么问题？或者在什么场景下需要这个功能？
      placeholder: "当我分析多个日志文件时，需要手动合并，非常繁琐..."
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: 期望的解决方案
      description: 描述你理想中的功能表现
      placeholder: |
        希望支持多文件输入：
        ```bash
        snaplog stats app1.log app2.log app3.log
        ```
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: 替代方案
      description: 你考虑过哪些替代方案？

  - type: dropdown
    id: scope
    attributes:
      label: 影响范围
      options:
        - 新命令
        - 现有命令增强
        - 输出格式
        - 性能优化
        - 文档改进
        - 其他
    validations:
      required: true

  - type: checkboxes
    id: contribution
    attributes:
      label: 参与意愿
      options:
        - label: 我愿意提交 PR 来实现这个功能
``` |  |
| +37.05 | Henry | Dispatching sub-agents for goal: Deliver the growth strategy for: 以下是团队上一轮的输出成果，请在保留优点的基础上，根据改进反馈重新输出全部文件。
每个文件用 === FILE: 文件名 === 作为分隔符开头，不要省略任何文件。



改进反馈：
README 缺少 stdin 管道用法说明（snaplog 应支持从 stdin 读取日志）；CONTRIBUTING 测试部分太简略，需要补充 conftest.py fixtures 使用示例；ARCHITECTURE.md 的扩展点章节可以加一个完整的自定义 Parser 示例代码

上一轮产出：

=== FILE: ARCHITECTURE.md ===
# 🏗️ snaplog 架构文档

本文档描述 snaplog 的内部架构，帮助贡献者快速理解代码组织和数据流。

---

## 目录结构

```
snaplog/
├── __init__.py          # 版本号、包元数据
├── cli.py               # Click 命令定义（入口）
├── parser.py            # 日志行解析引擎
├── filters.py           # 过滤器（级别、时间、正则）
├── stats.py             # 统计聚合逻辑
├── exporters.py         # JSON / CSV 导出器
├── formatters.py        # Rich 终端输出格式化
├── models.py            # 数据模型（LogEntry dataclass）
└── utils.py             # 时间解析、文件探测等工具函数
tests/
├── conftest.py          # pytest fixtures
├── test_parser.py
├── test_filters.py
├── test_stats.py
├── test_exporters.py
└── test_cli.py
pyproject.toml           # 构建配置（PEP 621）
```

---

## 核心数据模型

```python
@dataclass(frozen=True, slots=True)
class LogEntry:
    timestamp: datetime | None
    level: str            # DEBUG / INFO / WARNING / ERROR / CRITICAL
    message: str
    raw: str              # 原始行文本
    line_number: int
```

所有模块围绕 `LogEntry` 进行流转，保持单一数据契约。

---

## 数据流

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌────────────┐
│  文件/   │────▶│  Parser  │────▶│ Filters  │────▶│ Formatter  │
│  stdin   │     │          │     │          │     │ / Exporter  │
└──────────┘     └──────────┘     └──────────┘     └────────────┘
                      │                                   │
                      │           ┌──────────┐            │
                      └──────────▶│  Stats   │────────────┘
                                  └──────────┘
```

1. **输入层** — `cli.py` 接收文件路径或 stdin，逐行读取。
2. **解析层** — `parser.py` 将原始文本行转为 `LogEntry`。支持多种格式自动探测，也可通过 `--pattern` 指定。
3. **过滤层** — `filters.py` 提供可组合的过滤器链（级别、时间范围）。过滤器实现为生成器，支持惰性求值，内存占用恒定。
4. **聚合层** — `stats.py` 对过滤后的条目做单遍扫描统计（计数、Top-N 等）。
5. **输出层** — `formatters.py`（Rich 表格输出到终端）或 `exporters.py`（JSON/CSV 写入文件）。

---

## 设计原则

| 原则 | 实践 |
|------|------|
| 流式处理 | 全链路使用 Python 生成器，处理 GB 级日志不爆内存 |
| 零外部依赖 | 运行时仅依赖 Click + Rich，均为纯 Python 包 |
| 可组合 | 每个过滤器/导出器独立，可自由组合 |
| 可测试 | 核心逻辑与 CLI 层解耦，纯函数优先 |
| 类型安全 | 全面使用 Python 3.10+ 类型标注，配合 mypy strict 模式 |

---

## CLI 层设计

使用 Click 的 `@group` + `@command` 模式：

```python
@click.group()
@click.option("--no-color", is_flag=True)
@click.pass_context
def cli(ctx, no_color): ...

@cli.command()
@click.option("--level", multiple=True)
@click.argument("logfile", type=click.Path(exists=True))
def filter(level, logfile): ...

@cli.command()
@click.option("--from", "--to", ...)
def slice(...): ...

@cli.command()
def stats(...): ...

@cli.command()
@click.option("--format", type=click.Choice(["json", "csv"]))
@click.option("--output", type=click.Path())
def export(...): ...
```

---

## 解析器架构

`parser.py` 采用策略模式：

```python
class ParserStrategy(Protocol):
    def parse(self, line: str, line_number: int) -> LogEntry | None: ...

class StandardParser:    ...   # "2026-02-24 10:03:12 ERROR msg"
class SyslogParser:      ...   # "Feb 24 10:03:12 host app[pid]: ERROR msg"
class CustomParser:      ...   # 用户自定义 pattern

def auto_detect(sample_lines: list[str]) -> ParserStrategy:
    """取前 10 行，逐一尝试各策略，返回匹配率最高的。"""
```

---

## 扩展点

- 新增日志格式：实现 `ParserStrategy` 协议即可。
- 新增导出格式：在 `exporters.py` 中添加导出函数，注册到 `--format` 的 `Choice` 列表。
- 新增过滤器：在 `filters.py` 中编写生成器函数，插入过滤链。


=== FILE: CONTRIBUTING.md ===
# 🤝 贡献指南

感谢你对 snaplog 的关注！无论是修复 typo 还是添加新功能，我们都非常欢迎。

---

## 快速开始

```bash
# 1. Fork 并克隆
git clone https://github.com/<your-username>/snaplog.git
cd snaplog

# 2. 创建虚拟环境
python3.10 -m venv .venv
source .venv/bin/activate

# 3. 安装开发依赖
pip install -e ".[dev]"

# 4. 确认测试通过
pytest
```

---

## 开发工作流

1. 从 `main` 创建功能分支：`git checkout -b feat/your-feature`
2. 编写代码 + 测试
3. 本地检查：
   ```bash
   pytest                # 单元测试
   mypy snaplog          # 类型检查
   ruff check snaplog    # 代码风格
   ruff format snaplog   # 自动格式化
   ```
4. 提交（遵循 Conventional Commits）：
   ```
   feat: add regex filter support
   fix: handle empty timestamp gracefully
   docs: update CLI usage examples
   ```
5. 推送并创建 Pull Request

---

## PR 规范

- 标题使用 Conventional Commits 格式
- 描述中说明「做了什么」和「为什么」
- 关联相关 Issue（`Closes #123`）
- 确保 CI 全绿（测试 + 类型检查 + lint）
- 新功能需附带测试，覆盖率不低于现有水平

---

## 代码风格

- 格式化：[Ruff](https://docs.astral.sh/ruff/)（行宽 88）
- 类型标注：所有公开函数必须有完整类型签名
- 文档字符串：Google 风格
- 命名：`snake_case`（函数/变量），`PascalCase`（类）

---

## 测试

```bash
# 运行全部测试
pytest

# 带覆盖率
pytest --cov=snaplog --cov-report=term-missing

# 只跑某个模块
pytest tests/test_parser.py -v
```

测试文件放在 `tests/` 目录，命名 `test_<module>.py`。使用 `conftest.py` 中的 fixtures 获取示例日志数据。

---

## Issue 与讨论

- Bug 报告：使用 [Bug Report 模板](.github/ISSUE_TEMPLATE/bug_report.yml)
- 功能建议：使用 [Feature Request 模板](.github/ISSUE_TEMPLATE/feature_request.yml)
- 一般讨论：在 GitHub Discussions 中发帖

---

## 行为准则

本项目遵循 [Contributor Covenant 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)。参与即表示你同意遵守该准则。

---

## 许可

你提交的所有贡献将按 MIT 许可证授权。


=== FILE: LAUNCH_PLAN.md ===
# 🚀 snaplog 开源发布计划

## 发布目标

将 snaplog 作为高质量 Python CLI 工具开源发布，建立初始社区，在发布后 30 天内达到 500 GitHub stars。

---

## 阶段一：发布准备（D-7 → D-Day）

| 事项 | 负责 | 状态 |
|------|------|------|
| 代码审查 & 清理（移除内部引用、硬编码路径） | Tech | ⬜ |
| 测试覆盖率 ≥ 90% | Tech | ⬜ |
| mypy strict + ruff 零警告 | Tech | ⬜ |
| pyproject.toml 元数据完善 | Tech | ⬜ |
| README / ARCHITECTURE / CONTRIBUTING 定稿 | PM | ⬜ |
| LICENSE (MIT) 文件 | PM | ⬜ |
| GitHub repo 设置（Topics、About、Social Preview） | PM | ⬜ |
| Issue 模板 & PR 模板 | PM | ⬜ |
| GitHub Actions CI（测试 + lint + 发布） | Tech | ⬜ |
| PyPI 账号 & trusted publisher 配置 | Tech | ⬜ |

---

## 阶段二：发布日（D-Day）

### 技术发布

1. 打 tag `v0.1.0`，触发 CI 自动发布到 PyPI
2. 确认 `pip install snaplog` 可用
3. 创建 GitHub Release，附 changelog

### 社区传播

| 渠道 | 内容策略 | 时间 |
|------|----------|------|
| Hacker News | "Show HN: snaplog – a fast CLI log analyzer in Python" | D-Day 上午 |
| Reddit r/Python | 功能演示 + GIF 动图 | D-Day 上午 |
| Reddit r/commandline | 侧重 CLI 体验和管道组合 | D-Day 下午 |
| Twitter/X | 30 秒演示视频 + 功能亮点线程 | D-Day |
| V2EX / 掘金 | 中文技术博文「用一条命令分析日志」 | D-Day |
| Dev.to | 英文教程 "Analyze logs like a pro with snaplog" | D+1 |

### 传播素材清单

- [ ] 终端录屏 GIF（[asciinema](https://asciinema.org/) 或 [VHS](https://github.com/charmbracelet/vhs)）
- [ ] 30 秒演示视频（MP4）
- [ ] 社交媒体配图（1200×630）
- [ ] 中文博文草稿
- [ ] 英文博文草稿

---

## 阶段三：发布后运营（D+1 → D+30）

### 第一周

- 每日检查 Issues，24 小时内首次回复
- 收集用户反馈，标记 `good first issue` 吸引贡献者
- 根据反馈发布 `v0.1.1` 热修复（如有必要）

### 第二周

- 发布「一周回顾」博文（数据：stars、downloads、issues、PRs）
- 在 Awesome Python / Awesome CLI 提交收录 PR
- 联系 2-3 位 Python 领域 KOL 试用

### 第三 & 四周

- 根据高票 Feature Request 规划 `v0.2.0`
- 建立 GitHub Discussions 或 Discord 社区频道
- 发布 `v0.2.0`（预计新增：正则过滤、多文件合并）

---

## 关键指标（D+30）

| 指标 | 目标 |
|------|------|
| GitHub Stars | 500+ |
| PyPI 周下载量 | 1,000+ |
| 已关闭 Issues | ≥ 70% |
| 外部贡献者 PR | ≥ 5 |
| 测试覆盖率 | ≥ 90% |

---

## 风险与应对

| 风险 | 应对 |
|------|------|
| 发布日无人关注 | 准备 B 计划：次日在不同时区重新发布到 HN |
| 大量 Issue 涌入 | 预设 label 体系 + 自动分类 bot |
| PyPI 发布失败 | 提前在 TestPyPI 验证完整流程 |
| 负面反馈（功能不足） | 路线图透明化，引导用户参与共建 |

---

*最后更新：2026-02-24*


=== FILE: README.md ===
<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/CLI-Click%20%2B%20Rich-orange" alt="Click + Rich">
</p>

# 📜 snaplog

**快如闪电的 CLI 日志分析工具。** 过滤、截取、统计、导出——一条命令搞定。

```
$ snaplog filter --level ERROR server.log
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Timestamp           ┃ Level ┃ Message                                ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 2026-02-24 10:03:12 │ ERROR │ Connection refused: db-primary:5432    │
│ 2026-02-24 10:05:44 │ ERROR │ Timeout waiting for response (30s)     │
└─────────────────────┴───────┴────────────────────────────────────────┘
```

---

## ✨ 功能一览

| 功能 | 命令 | 说明 |
|------|------|------|
| 按级别过滤 | `snaplog filter` | 支持 DEBUG / INFO / WARNING / ERROR / CRITICAL |
| 时间截取 | `snaplog slice` | 按起止时间截取日志片段 |
| 统计摘要 | `snaplog stats` | 各级别计数、时间跨度、高频消息 Top-N |
| 导出 | `snaplog export` | 导出为 JSON 或 CSV 格式 |

---

## 🚀 安装

```bash
pip install snaplog
```

或从源码安装：

```bash
git clone https://github.com/snaplog/snaplog.git
cd snaplog
pip install -e .
```

### 依赖

仅依赖 Python 标准库 + 两个轻量包（安装时自动拉取）：

- [Click](https://click.palletsprojects.com/) — CLI 框架
- [Rich](https://rich.readthedocs.io/) — 终端美化输出

无其他外部依赖。Python 3.10+ 即可运行。

---

## 📖 使用指南

### 按级别过滤

```bash
# 只看 ERROR 及以上
snaplog filter --level ERROR app.log

# 多级别
snaplog filter --level WARNING --level ERROR app.log
```

### 时间截取

```bash
# 截取某个时间窗口
snaplog slice --from "2026-02-24 09:00:00" --to "2026-02-24 12:00:00" app.log
```

### 统计摘要

```bash
snaplog stats app.log
```

输出示例：

```
Log Summary
───────────────────────────
Total lines   : 14,328
Time span     : 2026-02-23 00:00:01 → 2026-02-24 17:58:59
───────────────────────────
DEBUG         :  4,102  (28.6%)
INFO          :  8,541  (59.6%)
WARNING       :  1,203  ( 8.4%)
ERROR         :    412  ( 2.9%)
CRITICAL      :     70  ( 0.5%)
───────────────────────────
Top-5 Messages:
 1. "Connection reset by peer"          × 87
 2. "Retry attempt exceeded"            × 63
 ...
```

### 导出

```bash
# 导出为 JSON
snaplog export --format json --output result.json app.log

# 导出为 CSV
snaplog export --format csv --output result.csv app.log

# 可与 filter/slice 组合
snaplog filter --level ERROR app.log | snaplog export --format json --output errors.json -
```

### 全局选项

```bash
snaplog --help          # 查看所有命令
snaplog filter --help   # 查看子命令帮助
snaplog --no-color ...  # 禁用彩色输出（适合管道）
```

---

## 📐 日志格式支持

snaplog 自动识别以下常见格式：

```
# 标准格式
2026-02-24 10:03:12 ERROR Connection refused
# syslog 风格
Feb 24 10:03:12 hostname app[1234]: ERROR Connection refused
# 自定义分隔符（通过 --pattern 指定）
snaplog filter --pattern "{timestamp}|{level}|{message}" --level ERROR app.log
```

---

## 🗺️ 路线图

- [x] 按级别过滤
- [x] 时间截取
- [x] 统计摘要
- [x] JSON / CSV 导出
- [ ] 正则表达式过滤 (`--grep`)
- [ ] 多文件合并分析
- [ ] 实时尾部跟踪 (`snaplog tail`)
- [ ] 插件系统（自定义解析器）

---

## 🤝 参与贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解流程。

---

## 📄 许可证

[MIT License](LICENSE) © 2026 snaplog contributors


=== FILE: .github/ISSUE_TEMPLATE/bug_report.yml ===
```yaml
name: 🐛 Bug 报告
description: 报告 snaplog 的问题或异常行为
title: "[Bug]: "
labels: ["bug", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        感谢你花时间报告问题！请尽量填写以下信息，帮助我们快速定位。

  - type: input
    id: version
    attributes:
      label: snaplog 版本
      description: "运行 `snaplog --version` 获取"
      placeholder: "0.1.0"
    validations:
      required: true

  - type: input
    id: python-version
    attributes:
      label: Python 版本
      description: "运行 `python --version` 获取"
      placeholder: "3.10.12"
    validations:
      required: true

  - type: dropdown
    id: os
    attributes:
      label: 操作系统
      options:
        - macOS
        - Linux
        - Windows
        - 其他
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: 问题描述
      description: 清晰简洁地描述遇到的问题
    validations:
      required: true

  - type: textarea
    id: reproduce
    attributes:
      label: 复现步骤
      description: 提供最小复现步骤
      value: |
        1. 准备日志文件（内容示例）：
           ```
           2026-02-24 10:00:00 ERROR something broke
           ```
        2. 运行命令：
           ```bash
           snaplog filter --level ERROR test.log
           ```
        3. 观察到的行为：...
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: 期望行为
      description: 你期望发生什么？
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: 错误输出 / 堆栈信息
      description: 粘贴完整的终端输出
      render: shell

  - type: textarea
    id: additional
    attributes:
      label: 补充信息
      description: 任何有助于排查的额外上下文（截图、日志文件片段等）
```


=== FILE: .github/ISSUE_TEMPLATE/feature_request.yml ===
```yaml
name: ✨ 功能建议
description: 提出新功能或改进建议
title: "[Feature]: "
labels: ["enhancement"]
body:
  - type: markdown
    attributes:
      value: |
        感谢你的建议！好的想法让 snaplog 变得更好。

  - type: textarea
    id: problem
    attributes:
      label: 问题或动机
      description: 你想解决什么问题？或者在什么场景下需要这个功能？
      placeholder: "当我分析多个日志文件时，需要手动合并，非常繁琐..."
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: 期望的解决方案
      description: 描述你理想中的功能表现
      placeholder: |
        希望支持多文件输入：
        ```bash
        snaplog stats app1.log app2.log app3.log
        ```
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: 替代方案
      description: 你考虑过哪些替代方案？

  - type: dropdown
    id: scope
    attributes:
      label: 影响范围
      options:
        - 新命令
        - 现有命令增强
        - 输出格式
        - 性能优化
        - 文档改进
        - 其他
    validations:
      required: true

  - type: checkboxes
    id: contribution
    attributes:
      label: 参与意愿
      options:
        - label: 我愿意提交 PR 来实现这个功能
``` |  |
| +37.05 | Elon/Architecture | Received task: Design technical architecture for: Deliver the technical implementation plan for: 以下是团队上一轮的输出成果，请在保留优点的基础上，根据改进反馈重新输出全部文件。
每个文件用 === FILE: 文件名 === 作为分隔符开头，不要省略任何文件。



改进反馈：
README 缺少 stdin 管道用法说明（snaplog 应支持从 stdin 读取日志）；CONTRIBUTING 测试部分太简略，需要补充 conftest.py fixtures 使用示例；ARCHITECTURE.md 的扩展点章节可以加一个完整的自定义 Parser 示例代码

上一轮产出：

=== FILE: ARCHITECTURE.md ===
# 🏗️ snaplog 架构文档

本文档描述 snaplog 的内部架构，帮助贡献者快速理解代码组织和数据流。

---

## 目录结构

```
snaplog/
├── __init__.py          # 版本号、包元数据
├── cli.py               # Click 命令定义（入口）
├── parser.py            # 日志行解析引擎
├── filters.py           # 过滤器（级别、时间、正则）
├── stats.py             # 统计聚合逻辑
├── exporters.py         # JSON / CSV 导出器
├── formatters.py        # Rich 终端输出格式化
├── models.py            # 数据模型（LogEntry dataclass）
└── utils.py             # 时间解析、文件探测等工具函数
tests/
├── conftest.py          # pytest fixtures
├── test_parser.py
├── test_filters.py
├── test_stats.py
├── test_exporters.py
└── test_cli.py
pyproject.toml           # 构建配置（PEP 621）
```

---

## 核心数据模型

```python
@dataclass(frozen=True, slots=True)
class LogEntry:
    timestamp: datetime | None
    level: str            # DEBUG / INFO / WARNING / ERROR / CRITICAL
    message: str
    raw: str              # 原始行文本
    line_number: int
```

所有模块围绕 `LogEntry` 进行流转，保持单一数据契约。

---

## 数据流

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌────────────┐
│  文件/   │────▶│  Parser  │────▶│ Filters  │────▶│ Formatter  │
│  stdin   │     │          │     │          │     │ / Exporter  │
└──────────┘     └──────────┘     └──────────┘     └────────────┘
                      │                                   │
                      │           ┌──────────┐            │
                      └──────────▶│  Stats   │────────────┘
                                  └──────────┘
```

1. **输入层** — `cli.py` 接收文件路径或 stdin，逐行读取。
2. **解析层** — `parser.py` 将原始文本行转为 `LogEntry`。支持多种格式自动探测，也可通过 `--pattern` 指定。
3. **过滤层** — `filters.py` 提供可组合的过滤器链（级别、时间范围）。过滤器实现为生成器，支持惰性求值，内存占用恒定。
4. **聚合层** — `stats.py` 对过滤后的条目做单遍扫描统计（计数、Top-N 等）。
5. **输出层** — `formatters.py`（Rich 表格输出到终端）或 `exporters.py`（JSON/CSV 写入文件）。

---

## 设计原则

| 原则 | 实践 |
|------|------|
| 流式处理 | 全链路使用 Python 生成器，处理 GB 级日志不爆内存 |
| 零外部依赖 | 运行时仅依赖 Click + Rich，均为纯 Python 包 |
| 可组合 | 每个过滤器/导出器独立，可自由组合 |
| 可测试 | 核心逻辑与 CLI 层解耦，纯函数优先 |
| 类型安全 | 全面使用 Python 3.10+ 类型标注，配合 mypy strict 模式 |

---

## CLI 层设计

使用 Click 的 `@group` + `@command` 模式：

```python
@click.group()
@click.option("--no-color", is_flag=True)
@click.pass_context
def cli(ctx, no_color): ...

@cli.command()
@click.option("--level", multiple=True)
@click.argument("logfile", type=click.Path(exists=True))
def filter(level, logfile): ...

@cli.command()
@click.option("--from", "--to", ...)
def slice(...): ...

@cli.command()
def stats(...): ...

@cli.command()
@click.option("--format", type=click.Choice(["json", "csv"]))
@click.option("--output", type=click.Path())
def export(...): ...
```

---

## 解析器架构

`parser.py` 采用策略模式：

```python
class ParserStrategy(Protocol):
    def parse(self, line: str, line_number: int) -> LogEntry | None: ...

class StandardParser:    ...   # "2026-02-24 10:03:12 ERROR msg"
class SyslogParser:      ...   # "Feb 24 10:03:12 host app[pid]: ERROR msg"
class CustomParser:      ...   # 用户自定义 pattern

def auto_detect(sample_lines: list[str]) -> ParserStrategy:
    """取前 10 行，逐一尝试各策略，返回匹配率最高的。"""
```

---

## 扩展点

- 新增日志格式：实现 `ParserStrategy` 协议即可。
- 新增导出格式：在 `exporters.py` 中添加导出函数，注册到 `--format` 的 `Choice` 列表。
- 新增过滤器：在 `filters.py` 中编写生成器函数，插入过滤链。


=== FILE: CONTRIBUTING.md ===
# 🤝 贡献指南

感谢你对 snaplog 的关注！无论是修复 typo 还是添加新功能，我们都非常欢迎。

---

## 快速开始

```bash
# 1. Fork 并克隆
git clone https://github.com/<your-username>/snaplog.git
cd snaplog

# 2. 创建虚拟环境
python3.10 -m venv .venv
source .venv/bin/activate

# 3. 安装开发依赖
pip install -e ".[dev]"

# 4. 确认测试通过
pytest
```

---

## 开发工作流

1. 从 `main` 创建功能分支：`git checkout -b feat/your-feature`
2. 编写代码 + 测试
3. 本地检查：
   ```bash
   pytest                # 单元测试
   mypy snaplog          # 类型检查
   ruff check snaplog    # 代码风格
   ruff format snaplog   # 自动格式化
   ```
4. 提交（遵循 Conventional Commits）：
   ```
   feat: add regex filter support
   fix: handle empty timestamp gracefully
   docs: update CLI usage examples
   ```
5. 推送并创建 Pull Request

---

## PR 规范

- 标题使用 Conventional Commits 格式
- 描述中说明「做了什么」和「为什么」
- 关联相关 Issue（`Closes #123`）
- 确保 CI 全绿（测试 + 类型检查 + lint）
- 新功能需附带测试，覆盖率不低于现有水平

---

## 代码风格

- 格式化：[Ruff](https://docs.astral.sh/ruff/)（行宽 88）
- 类型标注：所有公开函数必须有完整类型签名
- 文档字符串：Google 风格
- 命名：`snake_case`（函数/变量），`PascalCase`（类）

---

## 测试

```bash
# 运行全部测试
pytest

# 带覆盖率
pytest --cov=snaplog --cov-report=term-missing

# 只跑某个模块
pytest tests/test_parser.py -v
```

测试文件放在 `tests/` 目录，命名 `test_<module>.py`。使用 `conftest.py` 中的 fixtures 获取示例日志数据。

---

## Issue 与讨论

- Bug 报告：使用 [Bug Report 模板](.github/ISSUE_TEMPLATE/bug_report.yml)
- 功能建议：使用 [Feature Request 模板](.github/ISSUE_TEMPLATE/feature_request.yml)
- 一般讨论：在 GitHub Discussions 中发帖

---

## 行为准则

本项目遵循 [Contributor Covenant 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)。参与即表示你同意遵守该准则。

---

## 许可

你提交的所有贡献将按 MIT 许可证授权。


=== FILE: LAUNCH_PLAN.md ===
# 🚀 snaplog 开源发布计划

## 发布目标

将 snaplog 作为高质量 Python CLI 工具开源发布，建立初始社区，在发布后 30 天内达到 500 GitHub stars。

---

## 阶段一：发布准备（D-7 → D-Day）

| 事项 | 负责 | 状态 |
|------|------|------|
| 代码审查 & 清理（移除内部引用、硬编码路径） | Tech | ⬜ |
| 测试覆盖率 ≥ 90% | Tech | ⬜ |
| mypy strict + ruff 零警告 | Tech | ⬜ |
| pyproject.toml 元数据完善 | Tech | ⬜ |
| README / ARCHITECTURE / CONTRIBUTING 定稿 | PM | ⬜ |
| LICENSE (MIT) 文件 | PM | ⬜ |
| GitHub repo 设置（Topics、About、Social Preview） | PM | ⬜ |
| Issue 模板 & PR 模板 | PM | ⬜ |
| GitHub Actions CI（测试 + lint + 发布） | Tech | ⬜ |
| PyPI 账号 & trusted publisher 配置 | Tech | ⬜ |

---

## 阶段二：发布日（D-Day）

### 技术发布

1. 打 tag `v0.1.0`，触发 CI 自动发布到 PyPI
2. 确认 `pip install snaplog` 可用
3. 创建 GitHub Release，附 changelog

### 社区传播

| 渠道 | 内容策略 | 时间 |
|------|----------|------|
| Hacker News | "Show HN: snaplog – a fast CLI log analyzer in Python" | D-Day 上午 |
| Reddit r/Python | 功能演示 + GIF 动图 | D-Day 上午 |
| Reddit r/commandline | 侧重 CLI 体验和管道组合 | D-Day 下午 |
| Twitter/X | 30 秒演示视频 + 功能亮点线程 | D-Day |
| V2EX / 掘金 | 中文技术博文「用一条命令分析日志」 | D-Day |
| Dev.to | 英文教程 "Analyze logs like a pro with snaplog" | D+1 |

### 传播素材清单

- [ ] 终端录屏 GIF（[asciinema](https://asciinema.org/) 或 [VHS](https://github.com/charmbracelet/vhs)）
- [ ] 30 秒演示视频（MP4）
- [ ] 社交媒体配图（1200×630）
- [ ] 中文博文草稿
- [ ] 英文博文草稿

---

## 阶段三：发布后运营（D+1 → D+30）

### 第一周

- 每日检查 Issues，24 小时内首次回复
- 收集用户反馈，标记 `good first issue` 吸引贡献者
- 根据反馈发布 `v0.1.1` 热修复（如有必要）

### 第二周

- 发布「一周回顾」博文（数据：stars、downloads、issues、PRs）
- 在 Awesome Python / Awesome CLI 提交收录 PR
- 联系 2-3 位 Python 领域 KOL 试用

### 第三 & 四周

- 根据高票 Feature Request 规划 `v0.2.0`
- 建立 GitHub Discussions 或 Discord 社区频道
- 发布 `v0.2.0`（预计新增：正则过滤、多文件合并）

---

## 关键指标（D+30）

| 指标 | 目标 |
|------|------|
| GitHub Stars | 500+ |
| PyPI 周下载量 | 1,000+ |
| 已关闭 Issues | ≥ 70% |
| 外部贡献者 PR | ≥ 5 |
| 测试覆盖率 | ≥ 90% |

---

## 风险与应对

| 风险 | 应对 |
|------|------|
| 发布日无人关注 | 准备 B 计划：次日在不同时区重新发布到 HN |
| 大量 Issue 涌入 | 预设 label 体系 + 自动分类 bot |
| PyPI 发布失败 | 提前在 TestPyPI 验证完整流程 |
| 负面反馈（功能不足） | 路线图透明化，引导用户参与共建 |

---

*最后更新：2026-02-24*


=== FILE: README.md ===
<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/CLI-Click%20%2B%20Rich-orange" alt="Click + Rich">
</p>

# 📜 snaplog

**快如闪电的 CLI 日志分析工具。** 过滤、截取、统计、导出——一条命令搞定。

```
$ snaplog filter --level ERROR server.log
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Timestamp           ┃ Level ┃ Message                                ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 2026-02-24 10:03:12 │ ERROR │ Connection refused: db-primary:5432    │
│ 2026-02-24 10:05:44 │ ERROR │ Timeout waiting for response (30s)     │
└─────────────────────┴───────┴────────────────────────────────────────┘
```

---

## ✨ 功能一览

| 功能 | 命令 | 说明 |
|------|------|------|
| 按级别过滤 | `snaplog filter` | 支持 DEBUG / INFO / WARNING / ERROR / CRITICAL |
| 时间截取 | `snaplog slice` | 按起止时间截取日志片段 |
| 统计摘要 | `snaplog stats` | 各级别计数、时间跨度、高频消息 Top-N |
| 导出 | `snaplog export` | 导出为 JSON 或 CSV 格式 |

---

## 🚀 安装

```bash
pip install snaplog
```

或从源码安装：

```bash
git clone https://github.com/snaplog/snaplog.git
cd snaplog
pip install -e .
```

### 依赖

仅依赖 Python 标准库 + 两个轻量包（安装时自动拉取）：

- [Click](https://click.palletsprojects.com/) — CLI 框架
- [Rich](https://rich.readthedocs.io/) — 终端美化输出

无其他外部依赖。Python 3.10+ 即可运行。

---

## 📖 使用指南

### 按级别过滤

```bash
# 只看 ERROR 及以上
snaplog filter --level ERROR app.log

# 多级别
snaplog filter --level WARNING --level ERROR app.log
```

### 时间截取

```bash
# 截取某个时间窗口
snaplog slice --from "2026-02-24 09:00:00" --to "2026-02-24 12:00:00" app.log
```

### 统计摘要

```bash
snaplog stats app.log
```

输出示例：

```
Log Summary
───────────────────────────
Total lines   : 14,328
Time span     : 2026-02-23 00:00:01 → 2026-02-24 17:58:59
───────────────────────────
DEBUG         :  4,102  (28.6%)
INFO          :  8,541  (59.6%)
WARNING       :  1,203  ( 8.4%)
ERROR         :    412  ( 2.9%)
CRITICAL      :     70  ( 0.5%)
───────────────────────────
Top-5 Messages:
 1. "Connection reset by peer"          × 87
 2. "Retry attempt exceeded"            × 63
 ...
```

### 导出

```bash
# 导出为 JSON
snaplog export --format json --output result.json app.log

# 导出为 CSV
snaplog export --format csv --output result.csv app.log

# 可与 filter/slice 组合
snaplog filter --level ERROR app.log | snaplog export --format json --output errors.json -
```

### 全局选项

```bash
snaplog --help          # 查看所有命令
snaplog filter --help   # 查看子命令帮助
snaplog --no-color ...  # 禁用彩色输出（适合管道）
```

---

## 📐 日志格式支持

snaplog 自动识别以下常见格式：

```
# 标准格式
2026-02-24 10:03:12 ERROR Connection refused
# syslog 风格
Feb 24 10:03:12 hostname app[1234]: ERROR Connection refused
# 自定义分隔符（通过 --pattern 指定）
snaplog filter --pattern "{timestamp}|{level}|{message}" --level ERROR app.log
```

---

## 🗺️ 路线图

- [x] 按级别过滤
- [x] 时间截取
- [x] 统计摘要
- [x] JSON / CSV 导出
- [ ] 正则表达式过滤 (`--grep`)
- [ ] 多文件合并分析
- [ ] 实时尾部跟踪 (`snaplog tail`)
- [ ] 插件系统（自定义解析器）

---

## 🤝 参与贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解流程。

---

## 📄 许可证

[MIT License](LICENSE) © 2026 snaplog contributors


=== FILE: .github/ISSUE_TEMPLATE/bug_report.yml ===
```yaml
name: 🐛 Bug 报告
description: 报告 snaplog 的问题或异常行为
title: "[Bug]: "
labels: ["bug", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        感谢你花时间报告问题！请尽量填写以下信息，帮助我们快速定位。

  - type: input
    id: version
    attributes:
      label: snaplog 版本
      description: "运行 `snaplog --version` 获取"
      placeholder: "0.1.0"
    validations:
      required: true

  - type: input
    id: python-version
    attributes:
      label: Python 版本
      description: "运行 `python --version` 获取"
      placeholder: "3.10.12"
    validations:
      required: true

  - type: dropdown
    id: os
    attributes:
      label: 操作系统
      options:
        - macOS
        - Linux
        - Windows
        - 其他
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: 问题描述
      description: 清晰简洁地描述遇到的问题
    validations:
      required: true

  - type: textarea
    id: reproduce
    attributes:
      label: 复现步骤
      description: 提供最小复现步骤
      value: |
        1. 准备日志文件（内容示例）：
           ```
           2026-02-24 10:00:00 ERROR something broke
           ```
        2. 运行命令：
           ```bash
           snaplog filter --level ERROR test.log
           ```
        3. 观察到的行为：...
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: 期望行为
      description: 你期望发生什么？
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: 错误输出 / 堆栈信息
      description: 粘贴完整的终端输出
      render: shell

  - type: textarea
    id: additional
    attributes:
      label: 补充信息
      description: 任何有助于排查的额外上下文（截图、日志文件片段等）
```


=== FILE: .github/ISSUE_TEMPLATE/feature_request.yml ===
```yaml
name: ✨ 功能建议
description: 提出新功能或改进建议
title: "[Feature]: "
labels: ["enhancement"]
body:
  - type: markdown
    attributes:
      value: |
        感谢你的建议！好的想法让 snaplog 变得更好。

  - type: textarea
    id: problem
    attributes:
      label: 问题或动机
      description: 你想解决什么问题？或者在什么场景下需要这个功能？
      placeholder: "当我分析多个日志文件时，需要手动合并，非常繁琐..."
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: 期望的解决方案
      description: 描述你理想中的功能表现
      placeholder: |
        希望支持多文件输入：
        ```bash
        snaplog stats app1.log app2.log app3.log
        ```
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: 替代方案
      description: 你考虑过哪些替代方案？

  - type: dropdown
    id: scope
    attributes:
      label: 影响范围
      options:
        - 新命令
        - 现有命令增强
        - 输出格式
        - 性能优化
        - 文档改进
        - 其他
    validations:
      required: true

  - type: checkboxes
    id: contribution
    attributes:
      label: 参与意愿
      options:
        - label: 我愿意提交 PR 来实现这个功能
``` |  |
| +37.05 | Elon/Architecture | 调用 LLM | model=claude-haiku-4-5 max_tokens=2048 |
| +37.05 | Elon/Review | Received task: Produce review and testing plan for: Deliver the technical implementation plan for: 以下是团队上一轮的输出成果，请在保留优点的基础上，根据改进反馈重新输出全部文件。
每个文件用 === FILE: 文件名 === 作为分隔符开头，不要省略任何文件。



改进反馈：
README 缺少 stdin 管道用法说明（snaplog 应支持从 stdin 读取日志）；CONTRIBUTING 测试部分太简略，需要补充 conftest.py fixtures 使用示例；ARCHITECTURE.md 的扩展点章节可以加一个完整的自定义 Parser 示例代码

上一轮产出：

=== FILE: ARCHITECTURE.md ===
# 🏗️ snaplog 架构文档

本文档描述 snaplog 的内部架构，帮助贡献者快速理解代码组织和数据流。

---

## 目录结构

```
snaplog/
├── __init__.py          # 版本号、包元数据
├── cli.py               # Click 命令定义（入口）
├── parser.py            # 日志行解析引擎
├── filters.py           # 过滤器（级别、时间、正则）
├── stats.py             # 统计聚合逻辑
├── exporters.py         # JSON / CSV 导出器
├── formatters.py        # Rich 终端输出格式化
├── models.py            # 数据模型（LogEntry dataclass）
└── utils.py             # 时间解析、文件探测等工具函数
tests/
├── conftest.py          # pytest fixtures
├── test_parser.py
├── test_filters.py
├── test_stats.py
├── test_exporters.py
└── test_cli.py
pyproject.toml           # 构建配置（PEP 621）
```

---

## 核心数据模型

```python
@dataclass(frozen=True, slots=True)
class LogEntry:
    timestamp: datetime | None
    level: str            # DEBUG / INFO / WARNING / ERROR / CRITICAL
    message: str
    raw: str              # 原始行文本
    line_number: int
```

所有模块围绕 `LogEntry` 进行流转，保持单一数据契约。

---

## 数据流

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌────────────┐
│  文件/   │────▶│  Parser  │────▶│ Filters  │────▶│ Formatter  │
│  stdin   │     │          │     │          │     │ / Exporter  │
└──────────┘     └──────────┘     └──────────┘     └────────────┘
                      │                                   │
                      │           ┌──────────┐            │
                      └──────────▶│  Stats   │────────────┘
                                  └──────────┘
```

1. **输入层** — `cli.py` 接收文件路径或 stdin，逐行读取。
2. **解析层** — `parser.py` 将原始文本行转为 `LogEntry`。支持多种格式自动探测，也可通过 `--pattern` 指定。
3. **过滤层** — `filters.py` 提供可组合的过滤器链（级别、时间范围）。过滤器实现为生成器，支持惰性求值，内存占用恒定。
4. **聚合层** — `stats.py` 对过滤后的条目做单遍扫描统计（计数、Top-N 等）。
5. **输出层** — `formatters.py`（Rich 表格输出到终端）或 `exporters.py`（JSON/CSV 写入文件）。

---

## 设计原则

| 原则 | 实践 |
|------|------|
| 流式处理 | 全链路使用 Python 生成器，处理 GB 级日志不爆内存 |
| 零外部依赖 | 运行时仅依赖 Click + Rich，均为纯 Python 包 |
| 可组合 | 每个过滤器/导出器独立，可自由组合 |
| 可测试 | 核心逻辑与 CLI 层解耦，纯函数优先 |
| 类型安全 | 全面使用 Python 3.10+ 类型标注，配合 mypy strict 模式 |

---

## CLI 层设计

使用 Click 的 `@group` + `@command` 模式：

```python
@click.group()
@click.option("--no-color", is_flag=True)
@click.pass_context
def cli(ctx, no_color): ...

@cli.command()
@click.option("--level", multiple=True)
@click.argument("logfile", type=click.Path(exists=True))
def filter(level, logfile): ...

@cli.command()
@click.option("--from", "--to", ...)
def slice(...): ...

@cli.command()
def stats(...): ...

@cli.command()
@click.option("--format", type=click.Choice(["json", "csv"]))
@click.option("--output", type=click.Path())
def export(...): ...
```

---

## 解析器架构

`parser.py` 采用策略模式：

```python
class ParserStrategy(Protocol):
    def parse(self, line: str, line_number: int) -> LogEntry | None: ...

class StandardParser:    ...   # "2026-02-24 10:03:12 ERROR msg"
class SyslogParser:      ...   # "Feb 24 10:03:12 host app[pid]: ERROR msg"
class CustomParser:      ...   # 用户自定义 pattern

def auto_detect(sample_lines: list[str]) -> ParserStrategy:
    """取前 10 行，逐一尝试各策略，返回匹配率最高的。"""
```

---

## 扩展点

- 新增日志格式：实现 `ParserStrategy` 协议即可。
- 新增导出格式：在 `exporters.py` 中添加导出函数，注册到 `--format` 的 `Choice` 列表。
- 新增过滤器：在 `filters.py` 中编写生成器函数，插入过滤链。


=== FILE: CONTRIBUTING.md ===
# 🤝 贡献指南

感谢你对 snaplog 的关注！无论是修复 typo 还是添加新功能，我们都非常欢迎。

---

## 快速开始

```bash
# 1. Fork 并克隆
git clone https://github.com/<your-username>/snaplog.git
cd snaplog

# 2. 创建虚拟环境
python3.10 -m venv .venv
source .venv/bin/activate

# 3. 安装开发依赖
pip install -e ".[dev]"

# 4. 确认测试通过
pytest
```

---

## 开发工作流

1. 从 `main` 创建功能分支：`git checkout -b feat/your-feature`
2. 编写代码 + 测试
3. 本地检查：
   ```bash
   pytest                # 单元测试
   mypy snaplog          # 类型检查
   ruff check snaplog    # 代码风格
   ruff format snaplog   # 自动格式化
   ```
4. 提交（遵循 Conventional Commits）：
   ```
   feat: add regex filter support
   fix: handle empty timestamp gracefully
   docs: update CLI usage examples
   ```
5. 推送并创建 Pull Request

---

## PR 规范

- 标题使用 Conventional Commits 格式
- 描述中说明「做了什么」和「为什么」
- 关联相关 Issue（`Closes #123`）
- 确保 CI 全绿（测试 + 类型检查 + lint）
- 新功能需附带测试，覆盖率不低于现有水平

---

## 代码风格

- 格式化：[Ruff](https://docs.astral.sh/ruff/)（行宽 88）
- 类型标注：所有公开函数必须有完整类型签名
- 文档字符串：Google 风格
- 命名：`snake_case`（函数/变量），`PascalCase`（类）

---

## 测试

```bash
# 运行全部测试
pytest

# 带覆盖率
pytest --cov=snaplog --cov-report=term-missing

# 只跑某个模块
pytest tests/test_parser.py -v
```

测试文件放在 `tests/` 目录，命名 `test_<module>.py`。使用 `conftest.py` 中的 fixtures 获取示例日志数据。

---

## Issue 与讨论

- Bug 报告：使用 [Bug Report 模板](.github/ISSUE_TEMPLATE/bug_report.yml)
- 功能建议：使用 [Feature Request 模板](.github/ISSUE_TEMPLATE/feature_request.yml)
- 一般讨论：在 GitHub Discussions 中发帖

---

## 行为准则

本项目遵循 [Contributor Covenant 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)。参与即表示你同意遵守该准则。

---

## 许可

你提交的所有贡献将按 MIT 许可证授权。


=== FILE: LAUNCH_PLAN.md ===
# 🚀 snaplog 开源发布计划

## 发布目标

将 snaplog 作为高质量 Python CLI 工具开源发布，建立初始社区，在发布后 30 天内达到 500 GitHub stars。

---

## 阶段一：发布准备（D-7 → D-Day）

| 事项 | 负责 | 状态 |
|------|------|------|
| 代码审查 & 清理（移除内部引用、硬编码路径） | Tech | ⬜ |
| 测试覆盖率 ≥ 90% | Tech | ⬜ |
| mypy strict + ruff 零警告 | Tech | ⬜ |
| pyproject.toml 元数据完善 | Tech | ⬜ |
| README / ARCHITECTURE / CONTRIBUTING 定稿 | PM | ⬜ |
| LICENSE (MIT) 文件 | PM | ⬜ |
| GitHub repo 设置（Topics、About、Social Preview） | PM | ⬜ |
| Issue 模板 & PR 模板 | PM | ⬜ |
| GitHub Actions CI（测试 + lint + 发布） | Tech | ⬜ |
| PyPI 账号 & trusted publisher 配置 | Tech | ⬜ |

---

## 阶段二：发布日（D-Day）

### 技术发布

1. 打 tag `v0.1.0`，触发 CI 自动发布到 PyPI
2. 确认 `pip install snaplog` 可用
3. 创建 GitHub Release，附 changelog

### 社区传播

| 渠道 | 内容策略 | 时间 |
|------|----------|------|
| Hacker News | "Show HN: snaplog – a fast CLI log analyzer in Python" | D-Day 上午 |
| Reddit r/Python | 功能演示 + GIF 动图 | D-Day 上午 |
| Reddit r/commandline | 侧重 CLI 体验和管道组合 | D-Day 下午 |
| Twitter/X | 30 秒演示视频 + 功能亮点线程 | D-Day |
| V2EX / 掘金 | 中文技术博文「用一条命令分析日志」 | D-Day |
| Dev.to | 英文教程 "Analyze logs like a pro with snaplog" | D+1 |

### 传播素材清单

- [ ] 终端录屏 GIF（[asciinema](https://asciinema.org/) 或 [VHS](https://github.com/charmbracelet/vhs)）
- [ ] 30 秒演示视频（MP4）
- [ ] 社交媒体配图（1200×630）
- [ ] 中文博文草稿
- [ ] 英文博文草稿

---

## 阶段三：发布后运营（D+1 → D+30）

### 第一周

- 每日检查 Issues，24 小时内首次回复
- 收集用户反馈，标记 `good first issue` 吸引贡献者
- 根据反馈发布 `v0.1.1` 热修复（如有必要）

### 第二周

- 发布「一周回顾」博文（数据：stars、downloads、issues、PRs）
- 在 Awesome Python / Awesome CLI 提交收录 PR
- 联系 2-3 位 Python 领域 KOL 试用

### 第三 & 四周

- 根据高票 Feature Request 规划 `v0.2.0`
- 建立 GitHub Discussions 或 Discord 社区频道
- 发布 `v0.2.0`（预计新增：正则过滤、多文件合并）

---

## 关键指标（D+30）

| 指标 | 目标 |
|------|------|
| GitHub Stars | 500+ |
| PyPI 周下载量 | 1,000+ |
| 已关闭 Issues | ≥ 70% |
| 外部贡献者 PR | ≥ 5 |
| 测试覆盖率 | ≥ 90% |

---

## 风险与应对

| 风险 | 应对 |
|------|------|
| 发布日无人关注 | 准备 B 计划：次日在不同时区重新发布到 HN |
| 大量 Issue 涌入 | 预设 label 体系 + 自动分类 bot |
| PyPI 发布失败 | 提前在 TestPyPI 验证完整流程 |
| 负面反馈（功能不足） | 路线图透明化，引导用户参与共建 |

---

*最后更新：2026-02-24*


=== FILE: README.md ===
<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/CLI-Click%20%2B%20Rich-orange" alt="Click + Rich">
</p>

# 📜 snaplog

**快如闪电的 CLI 日志分析工具。** 过滤、截取、统计、导出——一条命令搞定。

```
$ snaplog filter --level ERROR server.log
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Timestamp           ┃ Level ┃ Message                                ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 2026-02-24 10:03:12 │ ERROR │ Connection refused: db-primary:5432    │
│ 2026-02-24 10:05:44 │ ERROR │ Timeout waiting for response (30s)     │
└─────────────────────┴───────┴────────────────────────────────────────┘
```

---

## ✨ 功能一览

| 功能 | 命令 | 说明 |
|------|------|------|
| 按级别过滤 | `snaplog filter` | 支持 DEBUG / INFO / WARNING / ERROR / CRITICAL |
| 时间截取 | `snaplog slice` | 按起止时间截取日志片段 |
| 统计摘要 | `snaplog stats` | 各级别计数、时间跨度、高频消息 Top-N |
| 导出 | `snaplog export` | 导出为 JSON 或 CSV 格式 |

---

## 🚀 安装

```bash
pip install snaplog
```

或从源码安装：

```bash
git clone https://github.com/snaplog/snaplog.git
cd snaplog
pip install -e .
```

### 依赖

仅依赖 Python 标准库 + 两个轻量包（安装时自动拉取）：

- [Click](https://click.palletsprojects.com/) — CLI 框架
- [Rich](https://rich.readthedocs.io/) — 终端美化输出

无其他外部依赖。Python 3.10+ 即可运行。

---

## 📖 使用指南

### 按级别过滤

```bash
# 只看 ERROR 及以上
snaplog filter --level ERROR app.log

# 多级别
snaplog filter --level WARNING --level ERROR app.log
```

### 时间截取

```bash
# 截取某个时间窗口
snaplog slice --from "2026-02-24 09:00:00" --to "2026-02-24 12:00:00" app.log
```

### 统计摘要

```bash
snaplog stats app.log
```

输出示例：

```
Log Summary
───────────────────────────
Total lines   : 14,328
Time span     : 2026-02-23 00:00:01 → 2026-02-24 17:58:59
───────────────────────────
DEBUG         :  4,102  (28.6%)
INFO          :  8,541  (59.6%)
WARNING       :  1,203  ( 8.4%)
ERROR         :    412  ( 2.9%)
CRITICAL      :     70  ( 0.5%)
───────────────────────────
Top-5 Messages:
 1. "Connection reset by peer"          × 87
 2. "Retry attempt exceeded"            × 63
 ...
```

### 导出

```bash
# 导出为 JSON
snaplog export --format json --output result.json app.log

# 导出为 CSV
snaplog export --format csv --output result.csv app.log

# 可与 filter/slice 组合
snaplog filter --level ERROR app.log | snaplog export --format json --output errors.json -
```

### 全局选项

```bash
snaplog --help          # 查看所有命令
snaplog filter --help   # 查看子命令帮助
snaplog --no-color ...  # 禁用彩色输出（适合管道）
```

---

## 📐 日志格式支持

snaplog 自动识别以下常见格式：

```
# 标准格式
2026-02-24 10:03:12 ERROR Connection refused
# syslog 风格
Feb 24 10:03:12 hostname app[1234]: ERROR Connection refused
# 自定义分隔符（通过 --pattern 指定）
snaplog filter --pattern "{timestamp}|{level}|{message}" --level ERROR app.log
```

---

## 🗺️ 路线图

- [x] 按级别过滤
- [x] 时间截取
- [x] 统计摘要
- [x] JSON / CSV 导出
- [ ] 正则表达式过滤 (`--grep`)
- [ ] 多文件合并分析
- [ ] 实时尾部跟踪 (`snaplog tail`)
- [ ] 插件系统（自定义解析器）

---

## 🤝 参与贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解流程。

---

## 📄 许可证

[MIT License](LICENSE) © 2026 snaplog contributors


=== FILE: .github/ISSUE_TEMPLATE/bug_report.yml ===
```yaml
name: 🐛 Bug 报告
description: 报告 snaplog 的问题或异常行为
title: "[Bug]: "
labels: ["bug", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        感谢你花时间报告问题！请尽量填写以下信息，帮助我们快速定位。

  - type: input
    id: version
    attributes:
      label: snaplog 版本
      description: "运行 `snaplog --version` 获取"
      placeholder: "0.1.0"
    validations:
      required: true

  - type: input
    id: python-version
    attributes:
      label: Python 版本
      description: "运行 `python --version` 获取"
      placeholder: "3.10.12"
    validations:
      required: true

  - type: dropdown
    id: os
    attributes:
      label: 操作系统
      options:
        - macOS
        - Linux
        - Windows
        - 其他
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: 问题描述
      description: 清晰简洁地描述遇到的问题
    validations:
      required: true

  - type: textarea
    id: reproduce
    attributes:
      label: 复现步骤
      description: 提供最小复现步骤
      value: |
        1. 准备日志文件（内容示例）：
           ```
           2026-02-24 10:00:00 ERROR something broke
           ```
        2. 运行命令：
           ```bash
           snaplog filter --level ERROR test.log
           ```
        3. 观察到的行为：...
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: 期望行为
      description: 你期望发生什么？
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: 错误输出 / 堆栈信息
      description: 粘贴完整的终端输出
      render: shell

  - type: textarea
    id: additional
    attributes:
      label: 补充信息
      description: 任何有助于排查的额外上下文（截图、日志文件片段等）
```


=== FILE: .github/ISSUE_TEMPLATE/feature_request.yml ===
```yaml
name: ✨ 功能建议
description: 提出新功能或改进建议
title: "[Feature]: "
labels: ["enhancement"]
body:
  - type: markdown
    attributes:
      value: |
        感谢你的建议！好的想法让 snaplog 变得更好。

  - type: textarea
    id: problem
    attributes:
      label: 问题或动机
      description: 你想解决什么问题？或者在什么场景下需要这个功能？
      placeholder: "当我分析多个日志文件时，需要手动合并，非常繁琐..."
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: 期望的解决方案
      description: 描述你理想中的功能表现
      placeholder: |
        希望支持多文件输入：
        ```bash
        snaplog stats app1.log app2.log app3.log
        ```
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: 替代方案
      description: 你考虑过哪些替代方案？

  - type: dropdown
    id: scope
    attributes:
      label: 影响范围
      options:
        - 新命令
        - 现有命令增强
        - 输出格式
        - 性能优化
        - 文档改进
        - 其他
    validations:
      required: true

  - type: checkboxes
    id: contribution
    attributes:
      label: 参与意愿
      options:
        - label: 我愿意提交 PR 来实现这个功能
``` |  |
| +37.05 | Elon/Review | 调用 LLM | model=claude-haiku-4-5 max_tokens=2048 |
| +37.05 | Elon/Debug | Received task: List likely failure modes and fixes for: Deliver the technical implementation plan for: 以下是团队上一轮的输出成果，请在保留优点的基础上，根据改进反馈重新输出全部文件。
每个文件用 === FILE: 文件名 === 作为分隔符开头，不要省略任何文件。



改进反馈：
README 缺少 stdin 管道用法说明（snaplog 应支持从 stdin 读取日志）；CONTRIBUTING 测试部分太简略，需要补充 conftest.py fixtures 使用示例；ARCHITECTURE.md 的扩展点章节可以加一个完整的自定义 Parser 示例代码

上一轮产出：

=== FILE: ARCHITECTURE.md ===
# 🏗️ snaplog 架构文档

本文档描述 snaplog 的内部架构，帮助贡献者快速理解代码组织和数据流。

---

## 目录结构

```
snaplog/
├── __init__.py          # 版本号、包元数据
├── cli.py               # Click 命令定义（入口）
├── parser.py            # 日志行解析引擎
├── filters.py           # 过滤器（级别、时间、正则）
├── stats.py             # 统计聚合逻辑
├── exporters.py         # JSON / CSV 导出器
├── formatters.py        # Rich 终端输出格式化
├── models.py            # 数据模型（LogEntry dataclass）
└── utils.py             # 时间解析、文件探测等工具函数
tests/
├── conftest.py          # pytest fixtures
├── test_parser.py
├── test_filters.py
├── test_stats.py
├── test_exporters.py
└── test_cli.py
pyproject.toml           # 构建配置（PEP 621）
```

---

## 核心数据模型

```python
@dataclass(frozen=True, slots=True)
class LogEntry:
    timestamp: datetime | None
    level: str            # DEBUG / INFO / WARNING / ERROR / CRITICAL
    message: str
    raw: str              # 原始行文本
    line_number: int
```

所有模块围绕 `LogEntry` 进行流转，保持单一数据契约。

---

## 数据流

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌────────────┐
│  文件/   │────▶│  Parser  │────▶│ Filters  │────▶│ Formatter  │
│  stdin   │     │          │     │          │     │ / Exporter  │
└──────────┘     └──────────┘     └──────────┘     └────────────┘
                      │                                   │
                      │           ┌──────────┐            │
                      └──────────▶│  Stats   │────────────┘
                                  └──────────┘
```

1. **输入层** — `cli.py` 接收文件路径或 stdin，逐行读取。
2. **解析层** — `parser.py` 将原始文本行转为 `LogEntry`。支持多种格式自动探测，也可通过 `--pattern` 指定。
3. **过滤层** — `filters.py` 提供可组合的过滤器链（级别、时间范围）。过滤器实现为生成器，支持惰性求值，内存占用恒定。
4. **聚合层** — `stats.py` 对过滤后的条目做单遍扫描统计（计数、Top-N 等）。
5. **输出层** — `formatters.py`（Rich 表格输出到终端）或 `exporters.py`（JSON/CSV 写入文件）。

---

## 设计原则

| 原则 | 实践 |
|------|------|
| 流式处理 | 全链路使用 Python 生成器，处理 GB 级日志不爆内存 |
| 零外部依赖 | 运行时仅依赖 Click + Rich，均为纯 Python 包 |
| 可组合 | 每个过滤器/导出器独立，可自由组合 |
| 可测试 | 核心逻辑与 CLI 层解耦，纯函数优先 |
| 类型安全 | 全面使用 Python 3.10+ 类型标注，配合 mypy strict 模式 |

---

## CLI 层设计

使用 Click 的 `@group` + `@command` 模式：

```python
@click.group()
@click.option("--no-color", is_flag=True)
@click.pass_context
def cli(ctx, no_color): ...

@cli.command()
@click.option("--level", multiple=True)
@click.argument("logfile", type=click.Path(exists=True))
def filter(level, logfile): ...

@cli.command()
@click.option("--from", "--to", ...)
def slice(...): ...

@cli.command()
def stats(...): ...

@cli.command()
@click.option("--format", type=click.Choice(["json", "csv"]))
@click.option("--output", type=click.Path())
def export(...): ...
```

---

## 解析器架构

`parser.py` 采用策略模式：

```python
class ParserStrategy(Protocol):
    def parse(self, line: str, line_number: int) -> LogEntry | None: ...

class StandardParser:    ...   # "2026-02-24 10:03:12 ERROR msg"
class SyslogParser:      ...   # "Feb 24 10:03:12 host app[pid]: ERROR msg"
class CustomParser:      ...   # 用户自定义 pattern

def auto_detect(sample_lines: list[str]) -> ParserStrategy:
    """取前 10 行，逐一尝试各策略，返回匹配率最高的。"""
```

---

## 扩展点

- 新增日志格式：实现 `ParserStrategy` 协议即可。
- 新增导出格式：在 `exporters.py` 中添加导出函数，注册到 `--format` 的 `Choice` 列表。
- 新增过滤器：在 `filters.py` 中编写生成器函数，插入过滤链。


=== FILE: CONTRIBUTING.md ===
# 🤝 贡献指南

感谢你对 snaplog 的关注！无论是修复 typo 还是添加新功能，我们都非常欢迎。

---

## 快速开始

```bash
# 1. Fork 并克隆
git clone https://github.com/<your-username>/snaplog.git
cd snaplog

# 2. 创建虚拟环境
python3.10 -m venv .venv
source .venv/bin/activate

# 3. 安装开发依赖
pip install -e ".[dev]"

# 4. 确认测试通过
pytest
```

---

## 开发工作流

1. 从 `main` 创建功能分支：`git checkout -b feat/your-feature`
2. 编写代码 + 测试
3. 本地检查：
   ```bash
   pytest                # 单元测试
   mypy snaplog          # 类型检查
   ruff check snaplog    # 代码风格
   ruff format snaplog   # 自动格式化
   ```
4. 提交（遵循 Conventional Commits）：
   ```
   feat: add regex filter support
   fix: handle empty timestamp gracefully
   docs: update CLI usage examples
   ```
5. 推送并创建 Pull Request

---

## PR 规范

- 标题使用 Conventional Commits 格式
- 描述中说明「做了什么」和「为什么」
- 关联相关 Issue（`Closes #123`）
- 确保 CI 全绿（测试 + 类型检查 + lint）
- 新功能需附带测试，覆盖率不低于现有水平

---

## 代码风格

- 格式化：[Ruff](https://docs.astral.sh/ruff/)（行宽 88）
- 类型标注：所有公开函数必须有完整类型签名
- 文档字符串：Google 风格
- 命名：`snake_case`（函数/变量），`PascalCase`（类）

---

## 测试

```bash
# 运行全部测试
pytest

# 带覆盖率
pytest --cov=snaplog --cov-report=term-missing

# 只跑某个模块
pytest tests/test_parser.py -v
```

测试文件放在 `tests/` 目录，命名 `test_<module>.py`。使用 `conftest.py` 中的 fixtures 获取示例日志数据。

---

## Issue 与讨论

- Bug 报告：使用 [Bug Report 模板](.github/ISSUE_TEMPLATE/bug_report.yml)
- 功能建议：使用 [Feature Request 模板](.github/ISSUE_TEMPLATE/feature_request.yml)
- 一般讨论：在 GitHub Discussions 中发帖

---

## 行为准则

本项目遵循 [Contributor Covenant 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)。参与即表示你同意遵守该准则。

---

## 许可

你提交的所有贡献将按 MIT 许可证授权。


=== FILE: LAUNCH_PLAN.md ===
# 🚀 snaplog 开源发布计划

## 发布目标

将 snaplog 作为高质量 Python CLI 工具开源发布，建立初始社区，在发布后 30 天内达到 500 GitHub stars。

---

## 阶段一：发布准备（D-7 → D-Day）

| 事项 | 负责 | 状态 |
|------|------|------|
| 代码审查 & 清理（移除内部引用、硬编码路径） | Tech | ⬜ |
| 测试覆盖率 ≥ 90% | Tech | ⬜ |
| mypy strict + ruff 零警告 | Tech | ⬜ |
| pyproject.toml 元数据完善 | Tech | ⬜ |
| README / ARCHITECTURE / CONTRIBUTING 定稿 | PM | ⬜ |
| LICENSE (MIT) 文件 | PM | ⬜ |
| GitHub repo 设置（Topics、About、Social Preview） | PM | ⬜ |
| Issue 模板 & PR 模板 | PM | ⬜ |
| GitHub Actions CI（测试 + lint + 发布） | Tech | ⬜ |
| PyPI 账号 & trusted publisher 配置 | Tech | ⬜ |

---

## 阶段二：发布日（D-Day）

### 技术发布

1. 打 tag `v0.1.0`，触发 CI 自动发布到 PyPI
2. 确认 `pip install snaplog` 可用
3. 创建 GitHub Release，附 changelog

### 社区传播

| 渠道 | 内容策略 | 时间 |
|------|----------|------|
| Hacker News | "Show HN: snaplog – a fast CLI log analyzer in Python" | D-Day 上午 |
| Reddit r/Python | 功能演示 + GIF 动图 | D-Day 上午 |
| Reddit r/commandline | 侧重 CLI 体验和管道组合 | D-Day 下午 |
| Twitter/X | 30 秒演示视频 + 功能亮点线程 | D-Day |
| V2EX / 掘金 | 中文技术博文「用一条命令分析日志」 | D-Day |
| Dev.to | 英文教程 "Analyze logs like a pro with snaplog" | D+1 |

### 传播素材清单

- [ ] 终端录屏 GIF（[asciinema](https://asciinema.org/) 或 [VHS](https://github.com/charmbracelet/vhs)）
- [ ] 30 秒演示视频（MP4）
- [ ] 社交媒体配图（1200×630）
- [ ] 中文博文草稿
- [ ] 英文博文草稿

---

## 阶段三：发布后运营（D+1 → D+30）

### 第一周

- 每日检查 Issues，24 小时内首次回复
- 收集用户反馈，标记 `good first issue` 吸引贡献者
- 根据反馈发布 `v0.1.1` 热修复（如有必要）

### 第二周

- 发布「一周回顾」博文（数据：stars、downloads、issues、PRs）
- 在 Awesome Python / Awesome CLI 提交收录 PR
- 联系 2-3 位 Python 领域 KOL 试用

### 第三 & 四周

- 根据高票 Feature Request 规划 `v0.2.0`
- 建立 GitHub Discussions 或 Discord 社区频道
- 发布 `v0.2.0`（预计新增：正则过滤、多文件合并）

---

## 关键指标（D+30）

| 指标 | 目标 |
|------|------|
| GitHub Stars | 500+ |
| PyPI 周下载量 | 1,000+ |
| 已关闭 Issues | ≥ 70% |
| 外部贡献者 PR | ≥ 5 |
| 测试覆盖率 | ≥ 90% |

---

## 风险与应对

| 风险 | 应对 |
|------|------|
| 发布日无人关注 | 准备 B 计划：次日在不同时区重新发布到 HN |
| 大量 Issue 涌入 | 预设 label 体系 + 自动分类 bot |
| PyPI 发布失败 | 提前在 TestPyPI 验证完整流程 |
| 负面反馈（功能不足） | 路线图透明化，引导用户参与共建 |

---

*最后更新：2026-02-24*


=== FILE: README.md ===
<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/CLI-Click%20%2B%20Rich-orange" alt="Click + Rich">
</p>

# 📜 snaplog

**快如闪电的 CLI 日志分析工具。** 过滤、截取、统计、导出——一条命令搞定。

```
$ snaplog filter --level ERROR server.log
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Timestamp           ┃ Level ┃ Message                                ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 2026-02-24 10:03:12 │ ERROR │ Connection refused: db-primary:5432    │
│ 2026-02-24 10:05:44 │ ERROR │ Timeout waiting for response (30s)     │
└─────────────────────┴───────┴────────────────────────────────────────┘
```

---

## ✨ 功能一览

| 功能 | 命令 | 说明 |
|------|------|------|
| 按级别过滤 | `snaplog filter` | 支持 DEBUG / INFO / WARNING / ERROR / CRITICAL |
| 时间截取 | `snaplog slice` | 按起止时间截取日志片段 |
| 统计摘要 | `snaplog stats` | 各级别计数、时间跨度、高频消息 Top-N |
| 导出 | `snaplog export` | 导出为 JSON 或 CSV 格式 |

---

## 🚀 安装

```bash
pip install snaplog
```

或从源码安装：

```bash
git clone https://github.com/snaplog/snaplog.git
cd snaplog
pip install -e .
```

### 依赖

仅依赖 Python 标准库 + 两个轻量包（安装时自动拉取）：

- [Click](https://click.palletsprojects.com/) — CLI 框架
- [Rich](https://rich.readthedocs.io/) — 终端美化输出

无其他外部依赖。Python 3.10+ 即可运行。

---

## 📖 使用指南

### 按级别过滤

```bash
# 只看 ERROR 及以上
snaplog filter --level ERROR app.log

# 多级别
snaplog filter --level WARNING --level ERROR app.log
```

### 时间截取

```bash
# 截取某个时间窗口
snaplog slice --from "2026-02-24 09:00:00" --to "2026-02-24 12:00:00" app.log
```

### 统计摘要

```bash
snaplog stats app.log
```

输出示例：

```
Log Summary
───────────────────────────
Total lines   : 14,328
Time span     : 2026-02-23 00:00:01 → 2026-02-24 17:58:59
───────────────────────────
DEBUG         :  4,102  (28.6%)
INFO          :  8,541  (59.6%)
WARNING       :  1,203  ( 8.4%)
ERROR         :    412  ( 2.9%)
CRITICAL      :     70  ( 0.5%)
───────────────────────────
Top-5 Messages:
 1. "Connection reset by peer"          × 87
 2. "Retry attempt exceeded"            × 63
 ...
```

### 导出

```bash
# 导出为 JSON
snaplog export --format json --output result.json app.log

# 导出为 CSV
snaplog export --format csv --output result.csv app.log

# 可与 filter/slice 组合
snaplog filter --level ERROR app.log | snaplog export --format json --output errors.json -
```

### 全局选项

```bash
snaplog --help          # 查看所有命令
snaplog filter --help   # 查看子命令帮助
snaplog --no-color ...  # 禁用彩色输出（适合管道）
```

---

## 📐 日志格式支持

snaplog 自动识别以下常见格式：

```
# 标准格式
2026-02-24 10:03:12 ERROR Connection refused
# syslog 风格
Feb 24 10:03:12 hostname app[1234]: ERROR Connection refused
# 自定义分隔符（通过 --pattern 指定）
snaplog filter --pattern "{timestamp}|{level}|{message}" --level ERROR app.log
```

---

## 🗺️ 路线图

- [x] 按级别过滤
- [x] 时间截取
- [x] 统计摘要
- [x] JSON / CSV 导出
- [ ] 正则表达式过滤 (`--grep`)
- [ ] 多文件合并分析
- [ ] 实时尾部跟踪 (`snaplog tail`)
- [ ] 插件系统（自定义解析器）

---

## 🤝 参与贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解流程。

---

## 📄 许可证

[MIT License](LICENSE) © 2026 snaplog contributors


=== FILE: .github/ISSUE_TEMPLATE/bug_report.yml ===
```yaml
name: 🐛 Bug 报告
description: 报告 snaplog 的问题或异常行为
title: "[Bug]: "
labels: ["bug", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        感谢你花时间报告问题！请尽量填写以下信息，帮助我们快速定位。

  - type: input
    id: version
    attributes:
      label: snaplog 版本
      description: "运行 `snaplog --version` 获取"
      placeholder: "0.1.0"
    validations:
      required: true

  - type: input
    id: python-version
    attributes:
      label: Python 版本
      description: "运行 `python --version` 获取"
      placeholder: "3.10.12"
    validations:
      required: true

  - type: dropdown
    id: os
    attributes:
      label: 操作系统
      options:
        - macOS
        - Linux
        - Windows
        - 其他
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: 问题描述
      description: 清晰简洁地描述遇到的问题
    validations:
      required: true

  - type: textarea
    id: reproduce
    attributes:
      label: 复现步骤
      description: 提供最小复现步骤
      value: |
        1. 准备日志文件（内容示例）：
           ```
           2026-02-24 10:00:00 ERROR something broke
           ```
        2. 运行命令：
           ```bash
           snaplog filter --level ERROR test.log
           ```
        3. 观察到的行为：...
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: 期望行为
      description: 你期望发生什么？
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: 错误输出 / 堆栈信息
      description: 粘贴完整的终端输出
      render: shell

  - type: textarea
    id: additional
    attributes:
      label: 补充信息
      description: 任何有助于排查的额外上下文（截图、日志文件片段等）
```


=== FILE: .github/ISSUE_TEMPLATE/feature_request.yml ===
```yaml
name: ✨ 功能建议
description: 提出新功能或改进建议
title: "[Feature]: "
labels: ["enhancement"]
body:
  - type: markdown
    attributes:
      value: |
        感谢你的建议！好的想法让 snaplog 变得更好。

  - type: textarea
    id: problem
    attributes:
      label: 问题或动机
      description: 你想解决什么问题？或者在什么场景下需要这个功能？
      placeholder: "当我分析多个日志文件时，需要手动合并，非常繁琐..."
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: 期望的解决方案
      description: 描述你理想中的功能表现
      placeholder: |
        希望支持多文件输入：
        ```bash
        snaplog stats app1.log app2.log app3.log
        ```
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: 替代方案
      description: 你考虑过哪些替代方案？

  - type: dropdown
    id: scope
    attributes:
      label: 影响范围
      options:
        - 新命令
        - 现有命令增强
        - 输出格式
        - 性能优化
        - 文档改进
        - 其他
    validations:
      required: true

  - type: checkboxes
    id: contribution
    attributes:
      label: 参与意愿
      options:
        - label: 我愿意提交 PR 来实现这个功能
``` |  |
| +37.06 | Elon/Debug | 调用 LLM | model=claude-haiku-4-5 max_tokens=2048 |
| +37.06 | Henry/Community | Received task: Create community operations plan for: Deliver the growth strategy for: 以下是团队上一轮的输出成果，请在保留优点的基础上，根据改进反馈重新输出全部文件。
每个文件用 === FILE: 文件名 === 作为分隔符开头，不要省略任何文件。



改进反馈：
README 缺少 stdin 管道用法说明（snaplog 应支持从 stdin 读取日志）；CONTRIBUTING 测试部分太简略，需要补充 conftest.py fixtures 使用示例；ARCHITECTURE.md 的扩展点章节可以加一个完整的自定义 Parser 示例代码

上一轮产出：

=== FILE: ARCHITECTURE.md ===
# 🏗️ snaplog 架构文档

本文档描述 snaplog 的内部架构，帮助贡献者快速理解代码组织和数据流。

---

## 目录结构

```
snaplog/
├── __init__.py          # 版本号、包元数据
├── cli.py               # Click 命令定义（入口）
├── parser.py            # 日志行解析引擎
├── filters.py           # 过滤器（级别、时间、正则）
├── stats.py             # 统计聚合逻辑
├── exporters.py         # JSON / CSV 导出器
├── formatters.py        # Rich 终端输出格式化
├── models.py            # 数据模型（LogEntry dataclass）
└── utils.py             # 时间解析、文件探测等工具函数
tests/
├── conftest.py          # pytest fixtures
├── test_parser.py
├── test_filters.py
├── test_stats.py
├── test_exporters.py
└── test_cli.py
pyproject.toml           # 构建配置（PEP 621）
```

---

## 核心数据模型

```python
@dataclass(frozen=True, slots=True)
class LogEntry:
    timestamp: datetime | None
    level: str            # DEBUG / INFO / WARNING / ERROR / CRITICAL
    message: str
    raw: str              # 原始行文本
    line_number: int
```

所有模块围绕 `LogEntry` 进行流转，保持单一数据契约。

---

## 数据流

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌────────────┐
│  文件/   │────▶│  Parser  │────▶│ Filters  │────▶│ Formatter  │
│  stdin   │     │          │     │          │     │ / Exporter  │
└──────────┘     └──────────┘     └──────────┘     └────────────┘
                      │                                   │
                      │           ┌──────────┐            │
                      └──────────▶│  Stats   │────────────┘
                                  └──────────┘
```

1. **输入层** — `cli.py` 接收文件路径或 stdin，逐行读取。
2. **解析层** — `parser.py` 将原始文本行转为 `LogEntry`。支持多种格式自动探测，也可通过 `--pattern` 指定。
3. **过滤层** — `filters.py` 提供可组合的过滤器链（级别、时间范围）。过滤器实现为生成器，支持惰性求值，内存占用恒定。
4. **聚合层** — `stats.py` 对过滤后的条目做单遍扫描统计（计数、Top-N 等）。
5. **输出层** — `formatters.py`（Rich 表格输出到终端）或 `exporters.py`（JSON/CSV 写入文件）。

---

## 设计原则

| 原则 | 实践 |
|------|------|
| 流式处理 | 全链路使用 Python 生成器，处理 GB 级日志不爆内存 |
| 零外部依赖 | 运行时仅依赖 Click + Rich，均为纯 Python 包 |
| 可组合 | 每个过滤器/导出器独立，可自由组合 |
| 可测试 | 核心逻辑与 CLI 层解耦，纯函数优先 |
| 类型安全 | 全面使用 Python 3.10+ 类型标注，配合 mypy strict 模式 |

---

## CLI 层设计

使用 Click 的 `@group` + `@command` 模式：

```python
@click.group()
@click.option("--no-color", is_flag=True)
@click.pass_context
def cli(ctx, no_color): ...

@cli.command()
@click.option("--level", multiple=True)
@click.argument("logfile", type=click.Path(exists=True))
def filter(level, logfile): ...

@cli.command()
@click.option("--from", "--to", ...)
def slice(...): ...

@cli.command()
def stats(...): ...

@cli.command()
@click.option("--format", type=click.Choice(["json", "csv"]))
@click.option("--output", type=click.Path())
def export(...): ...
```

---

## 解析器架构

`parser.py` 采用策略模式：

```python
class ParserStrategy(Protocol):
    def parse(self, line: str, line_number: int) -> LogEntry | None: ...

class StandardParser:    ...   # "2026-02-24 10:03:12 ERROR msg"
class SyslogParser:      ...   # "Feb 24 10:03:12 host app[pid]: ERROR msg"
class CustomParser:      ...   # 用户自定义 pattern

def auto_detect(sample_lines: list[str]) -> ParserStrategy:
    """取前 10 行，逐一尝试各策略，返回匹配率最高的。"""
```

---

## 扩展点

- 新增日志格式：实现 `ParserStrategy` 协议即可。
- 新增导出格式：在 `exporters.py` 中添加导出函数，注册到 `--format` 的 `Choice` 列表。
- 新增过滤器：在 `filters.py` 中编写生成器函数，插入过滤链。


=== FILE: CONTRIBUTING.md ===
# 🤝 贡献指南

感谢你对 snaplog 的关注！无论是修复 typo 还是添加新功能，我们都非常欢迎。

---

## 快速开始

```bash
# 1. Fork 并克隆
git clone https://github.com/<your-username>/snaplog.git
cd snaplog

# 2. 创建虚拟环境
python3.10 -m venv .venv
source .venv/bin/activate

# 3. 安装开发依赖
pip install -e ".[dev]"

# 4. 确认测试通过
pytest
```

---

## 开发工作流

1. 从 `main` 创建功能分支：`git checkout -b feat/your-feature`
2. 编写代码 + 测试
3. 本地检查：
   ```bash
   pytest                # 单元测试
   mypy snaplog          # 类型检查
   ruff check snaplog    # 代码风格
   ruff format snaplog   # 自动格式化
   ```
4. 提交（遵循 Conventional Commits）：
   ```
   feat: add regex filter support
   fix: handle empty timestamp gracefully
   docs: update CLI usage examples
   ```
5. 推送并创建 Pull Request

---

## PR 规范

- 标题使用 Conventional Commits 格式
- 描述中说明「做了什么」和「为什么」
- 关联相关 Issue（`Closes #123`）
- 确保 CI 全绿（测试 + 类型检查 + lint）
- 新功能需附带测试，覆盖率不低于现有水平

---

## 代码风格

- 格式化：[Ruff](https://docs.astral.sh/ruff/)（行宽 88）
- 类型标注：所有公开函数必须有完整类型签名
- 文档字符串：Google 风格
- 命名：`snake_case`（函数/变量），`PascalCase`（类）

---

## 测试

```bash
# 运行全部测试
pytest

# 带覆盖率
pytest --cov=snaplog --cov-report=term-missing

# 只跑某个模块
pytest tests/test_parser.py -v
```

测试文件放在 `tests/` 目录，命名 `test_<module>.py`。使用 `conftest.py` 中的 fixtures 获取示例日志数据。

---

## Issue 与讨论

- Bug 报告：使用 [Bug Report 模板](.github/ISSUE_TEMPLATE/bug_report.yml)
- 功能建议：使用 [Feature Request 模板](.github/ISSUE_TEMPLATE/feature_request.yml)
- 一般讨论：在 GitHub Discussions 中发帖

---

## 行为准则

本项目遵循 [Contributor Covenant 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)。参与即表示你同意遵守该准则。

---

## 许可

你提交的所有贡献将按 MIT 许可证授权。


=== FILE: LAUNCH_PLAN.md ===
# 🚀 snaplog 开源发布计划

## 发布目标

将 snaplog 作为高质量 Python CLI 工具开源发布，建立初始社区，在发布后 30 天内达到 500 GitHub stars。

---

## 阶段一：发布准备（D-7 → D-Day）

| 事项 | 负责 | 状态 |
|------|------|------|
| 代码审查 & 清理（移除内部引用、硬编码路径） | Tech | ⬜ |
| 测试覆盖率 ≥ 90% | Tech | ⬜ |
| mypy strict + ruff 零警告 | Tech | ⬜ |
| pyproject.toml 元数据完善 | Tech | ⬜ |
| README / ARCHITECTURE / CONTRIBUTING 定稿 | PM | ⬜ |
| LICENSE (MIT) 文件 | PM | ⬜ |
| GitHub repo 设置（Topics、About、Social Preview） | PM | ⬜ |
| Issue 模板 & PR 模板 | PM | ⬜ |
| GitHub Actions CI（测试 + lint + 发布） | Tech | ⬜ |
| PyPI 账号 & trusted publisher 配置 | Tech | ⬜ |

---

## 阶段二：发布日（D-Day）

### 技术发布

1. 打 tag `v0.1.0`，触发 CI 自动发布到 PyPI
2. 确认 `pip install snaplog` 可用
3. 创建 GitHub Release，附 changelog

### 社区传播

| 渠道 | 内容策略 | 时间 |
|------|----------|------|
| Hacker News | "Show HN: snaplog – a fast CLI log analyzer in Python" | D-Day 上午 |
| Reddit r/Python | 功能演示 + GIF 动图 | D-Day 上午 |
| Reddit r/commandline | 侧重 CLI 体验和管道组合 | D-Day 下午 |
| Twitter/X | 30 秒演示视频 + 功能亮点线程 | D-Day |
| V2EX / 掘金 | 中文技术博文「用一条命令分析日志」 | D-Day |
| Dev.to | 英文教程 "Analyze logs like a pro with snaplog" | D+1 |

### 传播素材清单

- [ ] 终端录屏 GIF（[asciinema](https://asciinema.org/) 或 [VHS](https://github.com/charmbracelet/vhs)）
- [ ] 30 秒演示视频（MP4）
- [ ] 社交媒体配图（1200×630）
- [ ] 中文博文草稿
- [ ] 英文博文草稿

---

## 阶段三：发布后运营（D+1 → D+30）

### 第一周

- 每日检查 Issues，24 小时内首次回复
- 收集用户反馈，标记 `good first issue` 吸引贡献者
- 根据反馈发布 `v0.1.1` 热修复（如有必要）

### 第二周

- 发布「一周回顾」博文（数据：stars、downloads、issues、PRs）
- 在 Awesome Python / Awesome CLI 提交收录 PR
- 联系 2-3 位 Python 领域 KOL 试用

### 第三 & 四周

- 根据高票 Feature Request 规划 `v0.2.0`
- 建立 GitHub Discussions 或 Discord 社区频道
- 发布 `v0.2.0`（预计新增：正则过滤、多文件合并）

---

## 关键指标（D+30）

| 指标 | 目标 |
|------|------|
| GitHub Stars | 500+ |
| PyPI 周下载量 | 1,000+ |
| 已关闭 Issues | ≥ 70% |
| 外部贡献者 PR | ≥ 5 |
| 测试覆盖率 | ≥ 90% |

---

## 风险与应对

| 风险 | 应对 |
|------|------|
| 发布日无人关注 | 准备 B 计划：次日在不同时区重新发布到 HN |
| 大量 Issue 涌入 | 预设 label 体系 + 自动分类 bot |
| PyPI 发布失败 | 提前在 TestPyPI 验证完整流程 |
| 负面反馈（功能不足） | 路线图透明化，引导用户参与共建 |

---

*最后更新：2026-02-24*


=== FILE: README.md ===
<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/CLI-Click%20%2B%20Rich-orange" alt="Click + Rich">
</p>

# 📜 snaplog

**快如闪电的 CLI 日志分析工具。** 过滤、截取、统计、导出——一条命令搞定。

```
$ snaplog filter --level ERROR server.log
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Timestamp           ┃ Level ┃ Message                                ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 2026-02-24 10:03:12 │ ERROR │ Connection refused: db-primary:5432    │
│ 2026-02-24 10:05:44 │ ERROR │ Timeout waiting for response (30s)     │
└─────────────────────┴───────┴────────────────────────────────────────┘
```

---

## ✨ 功能一览

| 功能 | 命令 | 说明 |
|------|------|------|
| 按级别过滤 | `snaplog filter` | 支持 DEBUG / INFO / WARNING / ERROR / CRITICAL |
| 时间截取 | `snaplog slice` | 按起止时间截取日志片段 |
| 统计摘要 | `snaplog stats` | 各级别计数、时间跨度、高频消息 Top-N |
| 导出 | `snaplog export` | 导出为 JSON 或 CSV 格式 |

---

## 🚀 安装

```bash
pip install snaplog
```

或从源码安装：

```bash
git clone https://github.com/snaplog/snaplog.git
cd snaplog
pip install -e .
```

### 依赖

仅依赖 Python 标准库 + 两个轻量包（安装时自动拉取）：

- [Click](https://click.palletsprojects.com/) — CLI 框架
- [Rich](https://rich.readthedocs.io/) — 终端美化输出

无其他外部依赖。Python 3.10+ 即可运行。

---

## 📖 使用指南

### 按级别过滤

```bash
# 只看 ERROR 及以上
snaplog filter --level ERROR app.log

# 多级别
snaplog filter --level WARNING --level ERROR app.log
```

### 时间截取

```bash
# 截取某个时间窗口
snaplog slice --from "2026-02-24 09:00:00" --to "2026-02-24 12:00:00" app.log
```

### 统计摘要

```bash
snaplog stats app.log
```

输出示例：

```
Log Summary
───────────────────────────
Total lines   : 14,328
Time span     : 2026-02-23 00:00:01 → 2026-02-24 17:58:59
───────────────────────────
DEBUG         :  4,102  (28.6%)
INFO          :  8,541  (59.6%)
WARNING       :  1,203  ( 8.4%)
ERROR         :    412  ( 2.9%)
CRITICAL      :     70  ( 0.5%)
───────────────────────────
Top-5 Messages:
 1. "Connection reset by peer"          × 87
 2. "Retry attempt exceeded"            × 63
 ...
```

### 导出

```bash
# 导出为 JSON
snaplog export --format json --output result.json app.log

# 导出为 CSV
snaplog export --format csv --output result.csv app.log

# 可与 filter/slice 组合
snaplog filter --level ERROR app.log | snaplog export --format json --output errors.json -
```

### 全局选项

```bash
snaplog --help          # 查看所有命令
snaplog filter --help   # 查看子命令帮助
snaplog --no-color ...  # 禁用彩色输出（适合管道）
```

---

## 📐 日志格式支持

snaplog 自动识别以下常见格式：

```
# 标准格式
2026-02-24 10:03:12 ERROR Connection refused
# syslog 风格
Feb 24 10:03:12 hostname app[1234]: ERROR Connection refused
# 自定义分隔符（通过 --pattern 指定）
snaplog filter --pattern "{timestamp}|{level}|{message}" --level ERROR app.log
```

---

## 🗺️ 路线图

- [x] 按级别过滤
- [x] 时间截取
- [x] 统计摘要
- [x] JSON / CSV 导出
- [ ] 正则表达式过滤 (`--grep`)
- [ ] 多文件合并分析
- [ ] 实时尾部跟踪 (`snaplog tail`)
- [ ] 插件系统（自定义解析器）

---

## 🤝 参与贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解流程。

---

## 📄 许可证

[MIT License](LICENSE) © 2026 snaplog contributors


=== FILE: .github/ISSUE_TEMPLATE/bug_report.yml ===
```yaml
name: 🐛 Bug 报告
description: 报告 snaplog 的问题或异常行为
title: "[Bug]: "
labels: ["bug", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        感谢你花时间报告问题！请尽量填写以下信息，帮助我们快速定位。

  - type: input
    id: version
    attributes:
      label: snaplog 版本
      description: "运行 `snaplog --version` 获取"
      placeholder: "0.1.0"
    validations:
      required: true

  - type: input
    id: python-version
    attributes:
      label: Python 版本
      description: "运行 `python --version` 获取"
      placeholder: "3.10.12"
    validations:
      required: true

  - type: dropdown
    id: os
    attributes:
      label: 操作系统
      options:
        - macOS
        - Linux
        - Windows
        - 其他
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: 问题描述
      description: 清晰简洁地描述遇到的问题
    validations:
      required: true

  - type: textarea
    id: reproduce
    attributes:
      label: 复现步骤
      description: 提供最小复现步骤
      value: |
        1. 准备日志文件（内容示例）：
           ```
           2026-02-24 10:00:00 ERROR something broke
           ```
        2. 运行命令：
           ```bash
           snaplog filter --level ERROR test.log
           ```
        3. 观察到的行为：...
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: 期望行为
      description: 你期望发生什么？
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: 错误输出 / 堆栈信息
      description: 粘贴完整的终端输出
      render: shell

  - type: textarea
    id: additional
    attributes:
      label: 补充信息
      description: 任何有助于排查的额外上下文（截图、日志文件片段等）
```


=== FILE: .github/ISSUE_TEMPLATE/feature_request.yml ===
```yaml
name: ✨ 功能建议
description: 提出新功能或改进建议
title: "[Feature]: "
labels: ["enhancement"]
body:
  - type: markdown
    attributes:
      value: |
        感谢你的建议！好的想法让 snaplog 变得更好。

  - type: textarea
    id: problem
    attributes:
      label: 问题或动机
      description: 你想解决什么问题？或者在什么场景下需要这个功能？
      placeholder: "当我分析多个日志文件时，需要手动合并，非常繁琐..."
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: 期望的解决方案
      description: 描述你理想中的功能表现
      placeholder: |
        希望支持多文件输入：
        ```bash
        snaplog stats app1.log app2.log app3.log
        ```
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: 替代方案
      description: 你考虑过哪些替代方案？

  - type: dropdown
    id: scope
    attributes:
      label: 影响范围
      options:
        - 新命令
        - 现有命令增强
        - 输出格式
        - 性能优化
        - 文档改进
        - 其他
    validations:
      required: true

  - type: checkboxes
    id: contribution
    attributes:
      label: 参与意愿
      options:
        - label: 我愿意提交 PR 来实现这个功能
``` |  |
| +37.06 | Henry/Community | 调用 LLM | model=claude-haiku-4-5 max_tokens=2048 |
| +37.06 | Henry/Content | Received task: Create content strategy for: Deliver the growth strategy for: 以下是团队上一轮的输出成果，请在保留优点的基础上，根据改进反馈重新输出全部文件。
每个文件用 === FILE: 文件名 === 作为分隔符开头，不要省略任何文件。



改进反馈：
README 缺少 stdin 管道用法说明（snaplog 应支持从 stdin 读取日志）；CONTRIBUTING 测试部分太简略，需要补充 conftest.py fixtures 使用示例；ARCHITECTURE.md 的扩展点章节可以加一个完整的自定义 Parser 示例代码

上一轮产出：

=== FILE: ARCHITECTURE.md ===
# 🏗️ snaplog 架构文档

本文档描述 snaplog 的内部架构，帮助贡献者快速理解代码组织和数据流。

---

## 目录结构

```
snaplog/
├── __init__.py          # 版本号、包元数据
├── cli.py               # Click 命令定义（入口）
├── parser.py            # 日志行解析引擎
├── filters.py           # 过滤器（级别、时间、正则）
├── stats.py             # 统计聚合逻辑
├── exporters.py         # JSON / CSV 导出器
├── formatters.py        # Rich 终端输出格式化
├── models.py            # 数据模型（LogEntry dataclass）
└── utils.py             # 时间解析、文件探测等工具函数
tests/
├── conftest.py          # pytest fixtures
├── test_parser.py
├── test_filters.py
├── test_stats.py
├── test_exporters.py
└── test_cli.py
pyproject.toml           # 构建配置（PEP 621）
```

---

## 核心数据模型

```python
@dataclass(frozen=True, slots=True)
class LogEntry:
    timestamp: datetime | None
    level: str            # DEBUG / INFO / WARNING / ERROR / CRITICAL
    message: str
    raw: str              # 原始行文本
    line_number: int
```

所有模块围绕 `LogEntry` 进行流转，保持单一数据契约。

---

## 数据流

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌────────────┐
│  文件/   │────▶│  Parser  │────▶│ Filters  │────▶│ Formatter  │
│  stdin   │     │          │     │          │     │ / Exporter  │
└──────────┘     └──────────┘     └──────────┘     └────────────┘
                      │                                   │
                      │           ┌──────────┐            │
                      └──────────▶│  Stats   │────────────┘
                                  └──────────┘
```

1. **输入层** — `cli.py` 接收文件路径或 stdin，逐行读取。
2. **解析层** — `parser.py` 将原始文本行转为 `LogEntry`。支持多种格式自动探测，也可通过 `--pattern` 指定。
3. **过滤层** — `filters.py` 提供可组合的过滤器链（级别、时间范围）。过滤器实现为生成器，支持惰性求值，内存占用恒定。
4. **聚合层** — `stats.py` 对过滤后的条目做单遍扫描统计（计数、Top-N 等）。
5. **输出层** — `formatters.py`（Rich 表格输出到终端）或 `exporters.py`（JSON/CSV 写入文件）。

---

## 设计原则

| 原则 | 实践 |
|------|------|
| 流式处理 | 全链路使用 Python 生成器，处理 GB 级日志不爆内存 |
| 零外部依赖 | 运行时仅依赖 Click + Rich，均为纯 Python 包 |
| 可组合 | 每个过滤器/导出器独立，可自由组合 |
| 可测试 | 核心逻辑与 CLI 层解耦，纯函数优先 |
| 类型安全 | 全面使用 Python 3.10+ 类型标注，配合 mypy strict 模式 |

---

## CLI 层设计

使用 Click 的 `@group` + `@command` 模式：

```python
@click.group()
@click.option("--no-color", is_flag=True)
@click.pass_context
def cli(ctx, no_color): ...

@cli.command()
@click.option("--level", multiple=True)
@click.argument("logfile", type=click.Path(exists=True))
def filter(level, logfile): ...

@cli.command()
@click.option("--from", "--to", ...)
def slice(...): ...

@cli.command()
def stats(...): ...

@cli.command()
@click.option("--format", type=click.Choice(["json", "csv"]))
@click.option("--output", type=click.Path())
def export(...): ...
```

---

## 解析器架构

`parser.py` 采用策略模式：

```python
class ParserStrategy(Protocol):
    def parse(self, line: str, line_number: int) -> LogEntry | None: ...

class StandardParser:    ...   # "2026-02-24 10:03:12 ERROR msg"
class SyslogParser:      ...   # "Feb 24 10:03:12 host app[pid]: ERROR msg"
class CustomParser:      ...   # 用户自定义 pattern

def auto_detect(sample_lines: list[str]) -> ParserStrategy:
    """取前 10 行，逐一尝试各策略，返回匹配率最高的。"""
```

---

## 扩展点

- 新增日志格式：实现 `ParserStrategy` 协议即可。
- 新增导出格式：在 `exporters.py` 中添加导出函数，注册到 `--format` 的 `Choice` 列表。
- 新增过滤器：在 `filters.py` 中编写生成器函数，插入过滤链。


=== FILE: CONTRIBUTING.md ===
# 🤝 贡献指南

感谢你对 snaplog 的关注！无论是修复 typo 还是添加新功能，我们都非常欢迎。

---

## 快速开始

```bash
# 1. Fork 并克隆
git clone https://github.com/<your-username>/snaplog.git
cd snaplog

# 2. 创建虚拟环境
python3.10 -m venv .venv
source .venv/bin/activate

# 3. 安装开发依赖
pip install -e ".[dev]"

# 4. 确认测试通过
pytest
```

---

## 开发工作流

1. 从 `main` 创建功能分支：`git checkout -b feat/your-feature`
2. 编写代码 + 测试
3. 本地检查：
   ```bash
   pytest                # 单元测试
   mypy snaplog          # 类型检查
   ruff check snaplog    # 代码风格
   ruff format snaplog   # 自动格式化
   ```
4. 提交（遵循 Conventional Commits）：
   ```
   feat: add regex filter support
   fix: handle empty timestamp gracefully
   docs: update CLI usage examples
   ```
5. 推送并创建 Pull Request

---

## PR 规范

- 标题使用 Conventional Commits 格式
- 描述中说明「做了什么」和「为什么」
- 关联相关 Issue（`Closes #123`）
- 确保 CI 全绿（测试 + 类型检查 + lint）
- 新功能需附带测试，覆盖率不低于现有水平

---

## 代码风格

- 格式化：[Ruff](https://docs.astral.sh/ruff/)（行宽 88）
- 类型标注：所有公开函数必须有完整类型签名
- 文档字符串：Google 风格
- 命名：`snake_case`（函数/变量），`PascalCase`（类）

---

## 测试

```bash
# 运行全部测试
pytest

# 带覆盖率
pytest --cov=snaplog --cov-report=term-missing

# 只跑某个模块
pytest tests/test_parser.py -v
```

测试文件放在 `tests/` 目录，命名 `test_<module>.py`。使用 `conftest.py` 中的 fixtures 获取示例日志数据。

---

## Issue 与讨论

- Bug 报告：使用 [Bug Report 模板](.github/ISSUE_TEMPLATE/bug_report.yml)
- 功能建议：使用 [Feature Request 模板](.github/ISSUE_TEMPLATE/feature_request.yml)
- 一般讨论：在 GitHub Discussions 中发帖

---

## 行为准则

本项目遵循 [Contributor Covenant 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)。参与即表示你同意遵守该准则。

---

## 许可

你提交的所有贡献将按 MIT 许可证授权。


=== FILE: LAUNCH_PLAN.md ===
# 🚀 snaplog 开源发布计划

## 发布目标

将 snaplog 作为高质量 Python CLI 工具开源发布，建立初始社区，在发布后 30 天内达到 500 GitHub stars。

---

## 阶段一：发布准备（D-7 → D-Day）

| 事项 | 负责 | 状态 |
|------|------|------|
| 代码审查 & 清理（移除内部引用、硬编码路径） | Tech | ⬜ |
| 测试覆盖率 ≥ 90% | Tech | ⬜ |
| mypy strict + ruff 零警告 | Tech | ⬜ |
| pyproject.toml 元数据完善 | Tech | ⬜ |
| README / ARCHITECTURE / CONTRIBUTING 定稿 | PM | ⬜ |
| LICENSE (MIT) 文件 | PM | ⬜ |
| GitHub repo 设置（Topics、About、Social Preview） | PM | ⬜ |
| Issue 模板 & PR 模板 | PM | ⬜ |
| GitHub Actions CI（测试 + lint + 发布） | Tech | ⬜ |
| PyPI 账号 & trusted publisher 配置 | Tech | ⬜ |

---

## 阶段二：发布日（D-Day）

### 技术发布

1. 打 tag `v0.1.0`，触发 CI 自动发布到 PyPI
2. 确认 `pip install snaplog` 可用
3. 创建 GitHub Release，附 changelog

### 社区传播

| 渠道 | 内容策略 | 时间 |
|------|----------|------|
| Hacker News | "Show HN: snaplog – a fast CLI log analyzer in Python" | D-Day 上午 |
| Reddit r/Python | 功能演示 + GIF 动图 | D-Day 上午 |
| Reddit r/commandline | 侧重 CLI 体验和管道组合 | D-Day 下午 |
| Twitter/X | 30 秒演示视频 + 功能亮点线程 | D-Day |
| V2EX / 掘金 | 中文技术博文「用一条命令分析日志」 | D-Day |
| Dev.to | 英文教程 "Analyze logs like a pro with snaplog" | D+1 |

### 传播素材清单

- [ ] 终端录屏 GIF（[asciinema](https://asciinema.org/) 或 [VHS](https://github.com/charmbracelet/vhs)）
- [ ] 30 秒演示视频（MP4）
- [ ] 社交媒体配图（1200×630）
- [ ] 中文博文草稿
- [ ] 英文博文草稿

---

## 阶段三：发布后运营（D+1 → D+30）

### 第一周

- 每日检查 Issues，24 小时内首次回复
- 收集用户反馈，标记 `good first issue` 吸引贡献者
- 根据反馈发布 `v0.1.1` 热修复（如有必要）

### 第二周

- 发布「一周回顾」博文（数据：stars、downloads、issues、PRs）
- 在 Awesome Python / Awesome CLI 提交收录 PR
- 联系 2-3 位 Python 领域 KOL 试用

### 第三 & 四周

- 根据高票 Feature Request 规划 `v0.2.0`
- 建立 GitHub Discussions 或 Discord 社区频道
- 发布 `v0.2.0`（预计新增：正则过滤、多文件合并）

---

## 关键指标（D+30）

| 指标 | 目标 |
|------|------|
| GitHub Stars | 500+ |
| PyPI 周下载量 | 1,000+ |
| 已关闭 Issues | ≥ 70% |
| 外部贡献者 PR | ≥ 5 |
| 测试覆盖率 | ≥ 90% |

---

## 风险与应对

| 风险 | 应对 |
|------|------|
| 发布日无人关注 | 准备 B 计划：次日在不同时区重新发布到 HN |
| 大量 Issue 涌入 | 预设 label 体系 + 自动分类 bot |
| PyPI 发布失败 | 提前在 TestPyPI 验证完整流程 |
| 负面反馈（功能不足） | 路线图透明化，引导用户参与共建 |

---

*最后更新：2026-02-24*


=== FILE: README.md ===
<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/CLI-Click%20%2B%20Rich-orange" alt="Click + Rich">
</p>

# 📜 snaplog

**快如闪电的 CLI 日志分析工具。** 过滤、截取、统计、导出——一条命令搞定。

```
$ snaplog filter --level ERROR server.log
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Timestamp           ┃ Level ┃ Message                                ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 2026-02-24 10:03:12 │ ERROR │ Connection refused: db-primary:5432    │
│ 2026-02-24 10:05:44 │ ERROR │ Timeout waiting for response (30s)     │
└─────────────────────┴───────┴────────────────────────────────────────┘
```

---

## ✨ 功能一览

| 功能 | 命令 | 说明 |
|------|------|------|
| 按级别过滤 | `snaplog filter` | 支持 DEBUG / INFO / WARNING / ERROR / CRITICAL |
| 时间截取 | `snaplog slice` | 按起止时间截取日志片段 |
| 统计摘要 | `snaplog stats` | 各级别计数、时间跨度、高频消息 Top-N |
| 导出 | `snaplog export` | 导出为 JSON 或 CSV 格式 |

---

## 🚀 安装

```bash
pip install snaplog
```

或从源码安装：

```bash
git clone https://github.com/snaplog/snaplog.git
cd snaplog
pip install -e .
```

### 依赖

仅依赖 Python 标准库 + 两个轻量包（安装时自动拉取）：

- [Click](https://click.palletsprojects.com/) — CLI 框架
- [Rich](https://rich.readthedocs.io/) — 终端美化输出

无其他外部依赖。Python 3.10+ 即可运行。

---

## 📖 使用指南

### 按级别过滤

```bash
# 只看 ERROR 及以上
snaplog filter --level ERROR app.log

# 多级别
snaplog filter --level WARNING --level ERROR app.log
```

### 时间截取

```bash
# 截取某个时间窗口
snaplog slice --from "2026-02-24 09:00:00" --to "2026-02-24 12:00:00" app.log
```

### 统计摘要

```bash
snaplog stats app.log
```

输出示例：

```
Log Summary
───────────────────────────
Total lines   : 14,328
Time span     : 2026-02-23 00:00:01 → 2026-02-24 17:58:59
───────────────────────────
DEBUG         :  4,102  (28.6%)
INFO          :  8,541  (59.6%)
WARNING       :  1,203  ( 8.4%)
ERROR         :    412  ( 2.9%)
CRITICAL      :     70  ( 0.5%)
───────────────────────────
Top-5 Messages:
 1. "Connection reset by peer"          × 87
 2. "Retry attempt exceeded"            × 63
 ...
```

### 导出

```bash
# 导出为 JSON
snaplog export --format json --output result.json app.log

# 导出为 CSV
snaplog export --format csv --output result.csv app.log

# 可与 filter/slice 组合
snaplog filter --level ERROR app.log | snaplog export --format json --output errors.json -
```

### 全局选项

```bash
snaplog --help          # 查看所有命令
snaplog filter --help   # 查看子命令帮助
snaplog --no-color ...  # 禁用彩色输出（适合管道）
```

---

## 📐 日志格式支持

snaplog 自动识别以下常见格式：

```
# 标准格式
2026-02-24 10:03:12 ERROR Connection refused
# syslog 风格
Feb 24 10:03:12 hostname app[1234]: ERROR Connection refused
# 自定义分隔符（通过 --pattern 指定）
snaplog filter --pattern "{timestamp}|{level}|{message}" --level ERROR app.log
```

---

## 🗺️ 路线图

- [x] 按级别过滤
- [x] 时间截取
- [x] 统计摘要
- [x] JSON / CSV 导出
- [ ] 正则表达式过滤 (`--grep`)
- [ ] 多文件合并分析
- [ ] 实时尾部跟踪 (`snaplog tail`)
- [ ] 插件系统（自定义解析器）

---

## 🤝 参与贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解流程。

---

## 📄 许可证

[MIT License](LICENSE) © 2026 snaplog contributors


=== FILE: .github/ISSUE_TEMPLATE/bug_report.yml ===
```yaml
name: 🐛 Bug 报告
description: 报告 snaplog 的问题或异常行为
title: "[Bug]: "
labels: ["bug", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        感谢你花时间报告问题！请尽量填写以下信息，帮助我们快速定位。

  - type: input
    id: version
    attributes:
      label: snaplog 版本
      description: "运行 `snaplog --version` 获取"
      placeholder: "0.1.0"
    validations:
      required: true

  - type: input
    id: python-version
    attributes:
      label: Python 版本
      description: "运行 `python --version` 获取"
      placeholder: "3.10.12"
    validations:
      required: true

  - type: dropdown
    id: os
    attributes:
      label: 操作系统
      options:
        - macOS
        - Linux
        - Windows
        - 其他
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: 问题描述
      description: 清晰简洁地描述遇到的问题
    validations:
      required: true

  - type: textarea
    id: reproduce
    attributes:
      label: 复现步骤
      description: 提供最小复现步骤
      value: |
        1. 准备日志文件（内容示例）：
           ```
           2026-02-24 10:00:00 ERROR something broke
           ```
        2. 运行命令：
           ```bash
           snaplog filter --level ERROR test.log
           ```
        3. 观察到的行为：...
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: 期望行为
      description: 你期望发生什么？
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: 错误输出 / 堆栈信息
      description: 粘贴完整的终端输出
      render: shell

  - type: textarea
    id: additional
    attributes:
      label: 补充信息
      description: 任何有助于排查的额外上下文（截图、日志文件片段等）
```


=== FILE: .github/ISSUE_TEMPLATE/feature_request.yml ===
```yaml
name: ✨ 功能建议
description: 提出新功能或改进建议
title: "[Feature]: "
labels: ["enhancement"]
body:
  - type: markdown
    attributes:
      value: |
        感谢你的建议！好的想法让 snaplog 变得更好。

  - type: textarea
    id: problem
    attributes:
      label: 问题或动机
      description: 你想解决什么问题？或者在什么场景下需要这个功能？
      placeholder: "当我分析多个日志文件时，需要手动合并，非常繁琐..."
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: 期望的解决方案
      description: 描述你理想中的功能表现
      placeholder: |
        希望支持多文件输入：
        ```bash
        snaplog stats app1.log app2.log app3.log
        ```
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: 替代方案
      description: 你考虑过哪些替代方案？

  - type: dropdown
    id: scope
    attributes:
      label: 影响范围
      options:
        - 新命令
        - 现有命令增强
        - 输出格式
        - 性能优化
        - 文档改进
        - 其他
    validations:
      required: true

  - type: checkboxes
    id: contribution
    attributes:
      label: 参与意愿
      options:
        - label: 我愿意提交 PR 来实现这个功能
``` |  |
| +37.06 | Henry/Content | 调用 LLM | model=claude-haiku-4-5 max_tokens=2048 |
| +37.06 | Henry/Analytics | Received task: Create analytics plan for: Deliver the growth strategy for: 以下是团队上一轮的输出成果，请在保留优点的基础上，根据改进反馈重新输出全部文件。
每个文件用 === FILE: 文件名 === 作为分隔符开头，不要省略任何文件。



改进反馈：
README 缺少 stdin 管道用法说明（snaplog 应支持从 stdin 读取日志）；CONTRIBUTING 测试部分太简略，需要补充 conftest.py fixtures 使用示例；ARCHITECTURE.md 的扩展点章节可以加一个完整的自定义 Parser 示例代码

上一轮产出：

=== FILE: ARCHITECTURE.md ===
# 🏗️ snaplog 架构文档

本文档描述 snaplog 的内部架构，帮助贡献者快速理解代码组织和数据流。

---

## 目录结构

```
snaplog/
├── __init__.py          # 版本号、包元数据
├── cli.py               # Click 命令定义（入口）
├── parser.py            # 日志行解析引擎
├── filters.py           # 过滤器（级别、时间、正则）
├── stats.py             # 统计聚合逻辑
├── exporters.py         # JSON / CSV 导出器
├── formatters.py        # Rich 终端输出格式化
├── models.py            # 数据模型（LogEntry dataclass）
└── utils.py             # 时间解析、文件探测等工具函数
tests/
├── conftest.py          # pytest fixtures
├── test_parser.py
├── test_filters.py
├── test_stats.py
├── test_exporters.py
└── test_cli.py
pyproject.toml           # 构建配置（PEP 621）
```

---

## 核心数据模型

```python
@dataclass(frozen=True, slots=True)
class LogEntry:
    timestamp: datetime | None
    level: str            # DEBUG / INFO / WARNING / ERROR / CRITICAL
    message: str
    raw: str              # 原始行文本
    line_number: int
```

所有模块围绕 `LogEntry` 进行流转，保持单一数据契约。

---

## 数据流

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌────────────┐
│  文件/   │────▶│  Parser  │────▶│ Filters  │────▶│ Formatter  │
│  stdin   │     │          │     │          │     │ / Exporter  │
└──────────┘     └──────────┘     └──────────┘     └────────────┘
                      │                                   │
                      │           ┌──────────┐            │
                      └──────────▶│  Stats   │────────────┘
                                  └──────────┘
```

1. **输入层** — `cli.py` 接收文件路径或 stdin，逐行读取。
2. **解析层** — `parser.py` 将原始文本行转为 `LogEntry`。支持多种格式自动探测，也可通过 `--pattern` 指定。
3. **过滤层** — `filters.py` 提供可组合的过滤器链（级别、时间范围）。过滤器实现为生成器，支持惰性求值，内存占用恒定。
4. **聚合层** — `stats.py` 对过滤后的条目做单遍扫描统计（计数、Top-N 等）。
5. **输出层** — `formatters.py`（Rich 表格输出到终端）或 `exporters.py`（JSON/CSV 写入文件）。

---

## 设计原则

| 原则 | 实践 |
|------|------|
| 流式处理 | 全链路使用 Python 生成器，处理 GB 级日志不爆内存 |
| 零外部依赖 | 运行时仅依赖 Click + Rich，均为纯 Python 包 |
| 可组合 | 每个过滤器/导出器独立，可自由组合 |
| 可测试 | 核心逻辑与 CLI 层解耦，纯函数优先 |
| 类型安全 | 全面使用 Python 3.10+ 类型标注，配合 mypy strict 模式 |

---

## CLI 层设计

使用 Click 的 `@group` + `@command` 模式：

```python
@click.group()
@click.option("--no-color", is_flag=True)
@click.pass_context
def cli(ctx, no_color): ...

@cli.command()
@click.option("--level", multiple=True)
@click.argument("logfile", type=click.Path(exists=True))
def filter(level, logfile): ...

@cli.command()
@click.option("--from", "--to", ...)
def slice(...): ...

@cli.command()
def stats(...): ...

@cli.command()
@click.option("--format", type=click.Choice(["json", "csv"]))
@click.option("--output", type=click.Path())
def export(...): ...
```

---

## 解析器架构

`parser.py` 采用策略模式：

```python
class ParserStrategy(Protocol):
    def parse(self, line: str, line_number: int) -> LogEntry | None: ...

class StandardParser:    ...   # "2026-02-24 10:03:12 ERROR msg"
class SyslogParser:      ...   # "Feb 24 10:03:12 host app[pid]: ERROR msg"
class CustomParser:      ...   # 用户自定义 pattern

def auto_detect(sample_lines: list[str]) -> ParserStrategy:
    """取前 10 行，逐一尝试各策略，返回匹配率最高的。"""
```

---

## 扩展点

- 新增日志格式：实现 `ParserStrategy` 协议即可。
- 新增导出格式：在 `exporters.py` 中添加导出函数，注册到 `--format` 的 `Choice` 列表。
- 新增过滤器：在 `filters.py` 中编写生成器函数，插入过滤链。


=== FILE: CONTRIBUTING.md ===
# 🤝 贡献指南

感谢你对 snaplog 的关注！无论是修复 typo 还是添加新功能，我们都非常欢迎。

---

## 快速开始

```bash
# 1. Fork 并克隆
git clone https://github.com/<your-username>/snaplog.git
cd snaplog

# 2. 创建虚拟环境
python3.10 -m venv .venv
source .venv/bin/activate

# 3. 安装开发依赖
pip install -e ".[dev]"

# 4. 确认测试通过
pytest
```

---

## 开发工作流

1. 从 `main` 创建功能分支：`git checkout -b feat/your-feature`
2. 编写代码 + 测试
3. 本地检查：
   ```bash
   pytest                # 单元测试
   mypy snaplog          # 类型检查
   ruff check snaplog    # 代码风格
   ruff format snaplog   # 自动格式化
   ```
4. 提交（遵循 Conventional Commits）：
   ```
   feat: add regex filter support
   fix: handle empty timestamp gracefully
   docs: update CLI usage examples
   ```
5. 推送并创建 Pull Request

---

## PR 规范

- 标题使用 Conventional Commits 格式
- 描述中说明「做了什么」和「为什么」
- 关联相关 Issue（`Closes #123`）
- 确保 CI 全绿（测试 + 类型检查 + lint）
- 新功能需附带测试，覆盖率不低于现有水平

---

## 代码风格

- 格式化：[Ruff](https://docs.astral.sh/ruff/)（行宽 88）
- 类型标注：所有公开函数必须有完整类型签名
- 文档字符串：Google 风格
- 命名：`snake_case`（函数/变量），`PascalCase`（类）

---

## 测试

```bash
# 运行全部测试
pytest

# 带覆盖率
pytest --cov=snaplog --cov-report=term-missing

# 只跑某个模块
pytest tests/test_parser.py -v
```

测试文件放在 `tests/` 目录，命名 `test_<module>.py`。使用 `conftest.py` 中的 fixtures 获取示例日志数据。

---

## Issue 与讨论

- Bug 报告：使用 [Bug Report 模板](.github/ISSUE_TEMPLATE/bug_report.yml)
- 功能建议：使用 [Feature Request 模板](.github/ISSUE_TEMPLATE/feature_request.yml)
- 一般讨论：在 GitHub Discussions 中发帖

---

## 行为准则

本项目遵循 [Contributor Covenant 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)。参与即表示你同意遵守该准则。

---

## 许可

你提交的所有贡献将按 MIT 许可证授权。


=== FILE: LAUNCH_PLAN.md ===
# 🚀 snaplog 开源发布计划

## 发布目标

将 snaplog 作为高质量 Python CLI 工具开源发布，建立初始社区，在发布后 30 天内达到 500 GitHub stars。

---

## 阶段一：发布准备（D-7 → D-Day）

| 事项 | 负责 | 状态 |
|------|------|------|
| 代码审查 & 清理（移除内部引用、硬编码路径） | Tech | ⬜ |
| 测试覆盖率 ≥ 90% | Tech | ⬜ |
| mypy strict + ruff 零警告 | Tech | ⬜ |
| pyproject.toml 元数据完善 | Tech | ⬜ |
| README / ARCHITECTURE / CONTRIBUTING 定稿 | PM | ⬜ |
| LICENSE (MIT) 文件 | PM | ⬜ |
| GitHub repo 设置（Topics、About、Social Preview） | PM | ⬜ |
| Issue 模板 & PR 模板 | PM | ⬜ |
| GitHub Actions CI（测试 + lint + 发布） | Tech | ⬜ |
| PyPI 账号 & trusted publisher 配置 | Tech | ⬜ |

---

## 阶段二：发布日（D-Day）

### 技术发布

1. 打 tag `v0.1.0`，触发 CI 自动发布到 PyPI
2. 确认 `pip install snaplog` 可用
3. 创建 GitHub Release，附 changelog

### 社区传播

| 渠道 | 内容策略 | 时间 |
|------|----------|------|
| Hacker News | "Show HN: snaplog – a fast CLI log analyzer in Python" | D-Day 上午 |
| Reddit r/Python | 功能演示 + GIF 动图 | D-Day 上午 |
| Reddit r/commandline | 侧重 CLI 体验和管道组合 | D-Day 下午 |
| Twitter/X | 30 秒演示视频 + 功能亮点线程 | D-Day |
| V2EX / 掘金 | 中文技术博文「用一条命令分析日志」 | D-Day |
| Dev.to | 英文教程 "Analyze logs like a pro with snaplog" | D+1 |

### 传播素材清单

- [ ] 终端录屏 GIF（[asciinema](https://asciinema.org/) 或 [VHS](https://github.com/charmbracelet/vhs)）
- [ ] 30 秒演示视频（MP4）
- [ ] 社交媒体配图（1200×630）
- [ ] 中文博文草稿
- [ ] 英文博文草稿

---

## 阶段三：发布后运营（D+1 → D+30）

### 第一周

- 每日检查 Issues，24 小时内首次回复
- 收集用户反馈，标记 `good first issue` 吸引贡献者
- 根据反馈发布 `v0.1.1` 热修复（如有必要）

### 第二周

- 发布「一周回顾」博文（数据：stars、downloads、issues、PRs）
- 在 Awesome Python / Awesome CLI 提交收录 PR
- 联系 2-3 位 Python 领域 KOL 试用

### 第三 & 四周

- 根据高票 Feature Request 规划 `v0.2.0`
- 建立 GitHub Discussions 或 Discord 社区频道
- 发布 `v0.2.0`（预计新增：正则过滤、多文件合并）

---

## 关键指标（D+30）

| 指标 | 目标 |
|------|------|
| GitHub Stars | 500+ |
| PyPI 周下载量 | 1,000+ |
| 已关闭 Issues | ≥ 70% |
| 外部贡献者 PR | ≥ 5 |
| 测试覆盖率 | ≥ 90% |

---

## 风险与应对

| 风险 | 应对 |
|------|------|
| 发布日无人关注 | 准备 B 计划：次日在不同时区重新发布到 HN |
| 大量 Issue 涌入 | 预设 label 体系 + 自动分类 bot |
| PyPI 发布失败 | 提前在 TestPyPI 验证完整流程 |
| 负面反馈（功能不足） | 路线图透明化，引导用户参与共建 |

---

*最后更新：2026-02-24*


=== FILE: README.md ===
<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/CLI-Click%20%2B%20Rich-orange" alt="Click + Rich">
</p>

# 📜 snaplog

**快如闪电的 CLI 日志分析工具。** 过滤、截取、统计、导出——一条命令搞定。

```
$ snaplog filter --level ERROR server.log
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Timestamp           ┃ Level ┃ Message                                ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 2026-02-24 10:03:12 │ ERROR │ Connection refused: db-primary:5432    │
│ 2026-02-24 10:05:44 │ ERROR │ Timeout waiting for response (30s)     │
└─────────────────────┴───────┴────────────────────────────────────────┘
```

---

## ✨ 功能一览

| 功能 | 命令 | 说明 |
|------|------|------|
| 按级别过滤 | `snaplog filter` | 支持 DEBUG / INFO / WARNING / ERROR / CRITICAL |
| 时间截取 | `snaplog slice` | 按起止时间截取日志片段 |
| 统计摘要 | `snaplog stats` | 各级别计数、时间跨度、高频消息 Top-N |
| 导出 | `snaplog export` | 导出为 JSON 或 CSV 格式 |

---

## 🚀 安装

```bash
pip install snaplog
```

或从源码安装：

```bash
git clone https://github.com/snaplog/snaplog.git
cd snaplog
pip install -e .
```

### 依赖

仅依赖 Python 标准库 + 两个轻量包（安装时自动拉取）：

- [Click](https://click.palletsprojects.com/) — CLI 框架
- [Rich](https://rich.readthedocs.io/) — 终端美化输出

无其他外部依赖。Python 3.10+ 即可运行。

---

## 📖 使用指南

### 按级别过滤

```bash
# 只看 ERROR 及以上
snaplog filter --level ERROR app.log

# 多级别
snaplog filter --level WARNING --level ERROR app.log
```

### 时间截取

```bash
# 截取某个时间窗口
snaplog slice --from "2026-02-24 09:00:00" --to "2026-02-24 12:00:00" app.log
```

### 统计摘要

```bash
snaplog stats app.log
```

输出示例：

```
Log Summary
───────────────────────────
Total lines   : 14,328
Time span     : 2026-02-23 00:00:01 → 2026-02-24 17:58:59
───────────────────────────
DEBUG         :  4,102  (28.6%)
INFO          :  8,541  (59.6%)
WARNING       :  1,203  ( 8.4%)
ERROR         :    412  ( 2.9%)
CRITICAL      :     70  ( 0.5%)
───────────────────────────
Top-5 Messages:
 1. "Connection reset by peer"          × 87
 2. "Retry attempt exceeded"            × 63
 ...
```

### 导出

```bash
# 导出为 JSON
snaplog export --format json --output result.json app.log

# 导出为 CSV
snaplog export --format csv --output result.csv app.log

# 可与 filter/slice 组合
snaplog filter --level ERROR app.log | snaplog export --format json --output errors.json -
```

### 全局选项

```bash
snaplog --help          # 查看所有命令
snaplog filter --help   # 查看子命令帮助
snaplog --no-color ...  # 禁用彩色输出（适合管道）
```

---

## 📐 日志格式支持

snaplog 自动识别以下常见格式：

```
# 标准格式
2026-02-24 10:03:12 ERROR Connection refused
# syslog 风格
Feb 24 10:03:12 hostname app[1234]: ERROR Connection refused
# 自定义分隔符（通过 --pattern 指定）
snaplog filter --pattern "{timestamp}|{level}|{message}" --level ERROR app.log
```

---

## 🗺️ 路线图

- [x] 按级别过滤
- [x] 时间截取
- [x] 统计摘要
- [x] JSON / CSV 导出
- [ ] 正则表达式过滤 (`--grep`)
- [ ] 多文件合并分析
- [ ] 实时尾部跟踪 (`snaplog tail`)
- [ ] 插件系统（自定义解析器）

---

## 🤝 参与贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解流程。

---

## 📄 许可证

[MIT License](LICENSE) © 2026 snaplog contributors


=== FILE: .github/ISSUE_TEMPLATE/bug_report.yml ===
```yaml
name: 🐛 Bug 报告
description: 报告 snaplog 的问题或异常行为
title: "[Bug]: "
labels: ["bug", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        感谢你花时间报告问题！请尽量填写以下信息，帮助我们快速定位。

  - type: input
    id: version
    attributes:
      label: snaplog 版本
      description: "运行 `snaplog --version` 获取"
      placeholder: "0.1.0"
    validations:
      required: true

  - type: input
    id: python-version
    attributes:
      label: Python 版本
      description: "运行 `python --version` 获取"
      placeholder: "3.10.12"
    validations:
      required: true

  - type: dropdown
    id: os
    attributes:
      label: 操作系统
      options:
        - macOS
        - Linux
        - Windows
        - 其他
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: 问题描述
      description: 清晰简洁地描述遇到的问题
    validations:
      required: true

  - type: textarea
    id: reproduce
    attributes:
      label: 复现步骤
      description: 提供最小复现步骤
      value: |
        1. 准备日志文件（内容示例）：
           ```
           2026-02-24 10:00:00 ERROR something broke
           ```
        2. 运行命令：
           ```bash
           snaplog filter --level ERROR test.log
           ```
        3. 观察到的行为：...
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: 期望行为
      description: 你期望发生什么？
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: 错误输出 / 堆栈信息
      description: 粘贴完整的终端输出
      render: shell

  - type: textarea
    id: additional
    attributes:
      label: 补充信息
      description: 任何有助于排查的额外上下文（截图、日志文件片段等）
```


=== FILE: .github/ISSUE_TEMPLATE/feature_request.yml ===
```yaml
name: ✨ 功能建议
description: 提出新功能或改进建议
title: "[Feature]: "
labels: ["enhancement"]
body:
  - type: markdown
    attributes:
      value: |
        感谢你的建议！好的想法让 snaplog 变得更好。

  - type: textarea
    id: problem
    attributes:
      label: 问题或动机
      description: 你想解决什么问题？或者在什么场景下需要这个功能？
      placeholder: "当我分析多个日志文件时，需要手动合并，非常繁琐..."
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: 期望的解决方案
      description: 描述你理想中的功能表现
      placeholder: |
        希望支持多文件输入：
        ```bash
        snaplog stats app1.log app2.log app3.log
        ```
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: 替代方案
      description: 你考虑过哪些替代方案？

  - type: dropdown
    id: scope
    attributes:
      label: 影响范围
      options:
        - 新命令
        - 现有命令增强
        - 输出格式
        - 性能优化
        - 文档改进
        - 其他
    validations:
      required: true

  - type: checkboxes
    id: contribution
    attributes:
      label: 参与意愿
      options:
        - label: 我愿意提交 PR 来实现这个功能
``` |  |
| +37.06 | Henry/Analytics | 调用 LLM | model=claude-haiku-4-5 max_tokens=2048 |
| +58.5 | Elon/Debug | LLM 响应完成 | 用时约 21.4s |
| +64.34 | Elon/Review | LLM 响应完成 | 用时约 27.3s |
| +90.24 | Henry/Analytics | LLM 响应完成 | 用时约 53.2s |
| +109.55 | Henry/Community | LLM 响应完成 | 用时约 72.5s |
| +130.11 | Henry/Content | LLM 响应完成 | 用时约 93.1s |
| +130.11 | Henry | 调用 LLM | model=claude-opus-4-6 max_tokens=4096 |
| +139.04 | Elon/Architecture | LLM 响应完成 | 用时约 102.0s |
| +139.04 | Elon | 调用 LLM | model=claude-opus-4-6 max_tokens=4096 |
| +161.61 | Henry | LLM 响应完成 | 用时约 31.5s |
| +168.02 | Elon | LLM 响应完成 | 用时约 29.0s |
| +168.02 | Echo | 调用 LLM | model=claude-opus-4-6 max_tokens=8192 |
| +530.57 | Echo | 请求失败，5s 后重试 (1/2)... [APITimeoutError] |  |
| +654.94 | Echo | LLM 响应完成 | 用时约 486.9s |
