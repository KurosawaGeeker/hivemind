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

### 运行测试

```bash
# 运行全部测试
pytest

# 带覆盖率
pytest --cov=snaplog --cov-report=term-missing

# 只跑某个模块
pytest tests/test_parser.py -v

# 只跑某个测试函数
pytest tests/test_parser.py::test_standard_format_parsing -v

# 跑标记为 slow 的测试
pytest -m slow
```

测试文件放在 `tests/` 目录，命名 `test_<module>.py`。

### conftest.py Fixtures 说明

`tests/conftest.py` 提供了一组可复用的 pytest fixtures，避免在每个测试文件中重复构造测试数据。以下是核心 fixtures 及其用法：

#### `sample_log_lines` — 原始日志行列表

返回一组覆盖各级别的标准格式日志行，适用于解析器和过滤器测试。

```python
# tests/conftest.py 中的定义
@pytest.fixture
def sample_log_lines() -> list[str]:
    """提供覆盖所有日志级别的标准格式示例行。"""
    return [
        "2026-02-24 10:00:00 DEBUG Starting up",
        "2026-02-24 10:00:01 INFO  Server listening on :8080",
        "2026-02-24 10:00:05 WARNING High memory usage: 89%",
        "2026-02-24 10:00:07 ERROR Connection refused: db:5432",
        "2026-02-24 10:00:10 CRITICAL Out of memory",
    ]

# 在测试中使用
def test_parser_handles_all_levels(sample_log_lines):
    """验证解析器能正确解析所有日志级别。"""
    parser = StandardParser()
    entries = [parser.parse(line, i) for i, line in enumerate(sample_log_lines)]
    levels = {e.level for e in entries if e is not None}
    assert levels == {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
```

#### `sample_entries` — 预解析的 LogEntry 列表

返回已解析好的 `LogEntry` 对象列表，适用于过滤器、统计和导出器测试（跳过解析步骤）。

```python
# tests/conftest.py 中的定义
@pytest.fixture
def sample_entries(sample_log_lines) -> list[LogEntry]:
    """将 sample_log_lines 预解析为 LogEntry 对象。"""
    parser = StandardParser()
    return [
        entry
        for i, line in enumerate(sample_log_lines)
        if (entry := parser.parse(line, i)) is not None
    ]

# 在测试中使用
def test_filter_by_level(sample_entries):
    """验证级别过滤器只保留指定级别。"""
    from snaplog.filters import filter_by_level

    errors = list(filter_by_level(iter(sample_entries), levels={"ERROR"}))
    assert len(errors) == 1
    assert errors[0].level == "ERROR"
    assert "Connection refused" in errors[0].message
```

#### `tmp_log_file` — 临时日志文件

创建一个写入了示例日志的临时文件，适用于 CLI 端到端测试和文件 I/O 测试。测试结束后自动清理。

```python
# tests/conftest.py 中的定义
@pytest.fixture
def tmp_log_file(tmp_path, sample_log_lines) -> Path:
    """创建包含示例日志的临时文件。"""
    log_file = tmp_path / "test.log"
    log_file.write_text("\n".join(sample_log_lines) + "\n")
    return log_file

# 在测试中使用（CLI 端到端测试）
from click.testing import CliRunner
from snaplog.cli import cli

def test_cli_filter_error(tmp_log_file):
    """验证 CLI filter 命令能正确过滤 ERROR 级别。"""
    runner = CliRunner()
    result = runner.invoke(cli, ["filter", "--level", "ERROR", str(tmp_log_file)])
    assert result.exit_code == 0
    assert "Connection refused" in result.output
    assert "DEBUG" not in result.output
```

#### `stdin_log_input` — 模拟 stdin 输入

提供模拟 stdin 管道输入的 fixture，适用于测试 stdin 读取功能。

```python
# tests/conftest.py 中的定义
@pytest.fixture
def stdin_log_input(sample_log_lines) -> str:
    """返回可用于模拟 stdin 的日志文本。"""
    return "\n".join(sample_log_lines) + "\n"

# 在测试中使用
def test_stdin_input(stdin_log_input):
    """验证 snaplog 能从 stdin 正确读取并过滤日志。"""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["filter", "--level", "ERROR", "-"],
        input=stdin_log_input,
    )
    assert result.exit_code == 0
    assert "Connection refused" in result.output
```

### 编写新测试的建议

- 优先使用 `conftest.py` 中的 fixtures，避免在测试函数中硬编码日志文本。
- 如果需要特殊格式的日志数据，在 `conftest.py` 中新增 fixture 并添加文档字符串。
- 测试命名遵循 `test_<被测行为>` 格式，如 `test_filter_by_level`、`test_export_json_format`。
- 每个测试只验证一个行为，保持测试函数简短。
- 使用 `@pytest.mark.slow` 标记耗时测试（如大文件处理）。

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
