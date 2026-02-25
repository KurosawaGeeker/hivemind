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
