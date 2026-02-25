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

1. **输入层** — `cli.py` 接收文件路径或 stdin，逐行读取。当文件参数为 `-` 或检测到 stdin 存在管道输入时，自动从 `sys.stdin` 逐行读取。
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

### 新增日志格式

实现 `ParserStrategy` 协议即可。以下是一个完整的自定义 Parser 示例——解析 Nginx access log 格式：

```python
# snaplog/parsers/nginx.py
"""Nginx access log 解析器示例。

支持的日志格式（默认 combined 格式）：
  172.16.0.1 - - [24/Feb/2026:10:03:12 +0000] "GET /api/health HTTP/1.1" 500 1234 "-" "curl/7.88"
"""

from __future__ import annotations

import re
from datetime import datetime
from snaplog.models import LogEntry

# Nginx combined log 正则
_NGINX_RE = re.compile(
    r'(?P<remote_addr>\S+)'       # 客户端 IP
    r' - (?P<remote_user>\S+)'    # 远程用户
    r' \[(?P<time>[^\]]+)\]'      # 时间戳 [24/Feb/2026:10:03:12 +0000]
    r' "(?P<request>[^"]*)"'      # 请求行 "GET /path HTTP/1.1"
    r' (?P<status>\d{3})'         # HTTP 状态码
    r' (?P<body_bytes>\d+)'       # 响应体大小
    r' "(?P<referer>[^"]*)"'      # Referer
    r' "(?P<user_agent>[^"]*)"'   # User-Agent
)

_NGINX_TIME_FMT = "%d/%b/%Y:%H:%M:%S %z"


def _status_to_level(status: int) -> str:
    """将 HTTP 状态码映射为日志级别。"""
    if status < 400:
        return "INFO"
    if status < 500:
        return "WARNING"
    return "ERROR"


class NginxAccessLogParser:
    """解析 Nginx access log（combined 格式）。

    实现 ParserStrategy 协议，可直接注册到 snaplog 解析器链。

    Usage:
        parser = NginxAccessLogParser()
        entry = parser.parse(
            '172.16.0.1 - - [24/Feb/2026:10:03:12 +0000] "GET /api HTTP/1.1" 500 1234 "-" "curl/7.88"',
            line_number=1,
        )
        assert entry is not None
        assert entry.level == "ERROR"
    """

    def parse(self, line: str, line_number: int) -> LogEntry | None:
        """解析单行 Nginx access log。

        Args:
            line: 原始日志行文本。
            line_number: 行号（从 0 开始）。

        Returns:
            解析成功返回 LogEntry，格式不匹配返回 None。
        """
        match = _NGINX_RE.match(line)
        if match is None:
            return None

        groups = match.groupdict()

        # 解析时间戳
        try:
            timestamp = datetime.strptime(groups["time"], _NGINX_TIME_FMT)
        except ValueError:
            timestamp = None

        status = int(groups["status"])
        level = _status_to_level(status)

        # 构造可读消息：请求行 + 状态码
        message = f'{groups["request"]} → {status} ({groups["body_bytes"]}B)'

        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            raw=line,
            line_number=line_number,
        )
```

将自定义解析器注册到 `auto_detect` 中：

```python
# 在 snaplog/parser.py 的 auto_detect 函数中添加
from snaplog.parsers.nginx import NginxAccessLogParser

_ALL_STRATEGIES: list[ParserStrategy] = [
    StandardParser(),
    SyslogParser(),
    NginxAccessLogParser(),   # ← 新增
]

def auto_detect(sample_lines: list[str]) -> ParserStrategy:
    """取前 10 行，逐一尝试各策略，返回匹配率最高的。"""
    best_strategy = _ALL_STRATEGIES[0]
    best_score = 0.0
    for strategy in _ALL_STRATEGIES:
        hits = sum(1 for line in sample_lines if strategy.parse(line, 0) is not None)
        score = hits / len(sample_lines) if sample_lines else 0.0
        if score > best_score:
            best_score = score
            best_strategy = strategy
    return best_strategy
```

### 新增导出格式

在 `exporters.py` 中添加导出函数，注册到 `--format` 的 `Choice` 列表。

### 新增过滤器

在 `filters.py` 中编写生成器函数，插入过滤链。
