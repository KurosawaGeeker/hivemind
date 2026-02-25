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
