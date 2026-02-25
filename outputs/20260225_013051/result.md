# 任务输出

**输入**: 为一个 Python 开源项目生成 README 和一份 GitHub Issue 模板

---

## Strategic Direction

目标明确：为 Python 开源项目生成高质量的 README.md 和 GitHub Issue 模板，同时建立早期社区增长框架。

核心决策：
- README 采用 6 段式结构（Hero → Quick Start → Features → Docs → Contributing → Badges），聚焦"5 分钟上手"体验
- Issue 模板覆盖 3 类场景：Bug Report / Feature Request / Question
- 增长策略以被动触达为主，不做主动推广，靠响应速度驱动自然增长飞轮

## Technical Track

Elon 返回空结果，技术交付物尚未生成。

待办：需要确认项目名称和功能描述后，由 Elon 输出以下文件：
1. `README.md`（6 段式结构）
2. `.github/ISSUE_TEMPLATE/bug_report.yml`
3. `.github/ISSUE_TEMPLATE/feature_request.yml`
4. `.github/ISSUE_TEMPLATE/question.yml`
5. `CONTRIBUTING.md`

## Growth Track

Henry 已交付完整的 30 天增长计划，关键要点：

- Week 1-2：开启 Discussions、24h 内首次响应所有 Issue、GitHub Actions 自动标签
- Week 3-4：沉淀案例至 `docs/examples.md`、发布 CONTRIBUTING.md 降低门槛
- 30 天目标：Stars +15-30%、Issue 首响 < 24h、新 Contributor +2-3 人
- 飞轮验证逻辑已内置：Star 增长不达标 → 优化 README；Issue 量低 → 检查可发现性；PR 转化低 → 简化贡献流程

## Risks

| 风险 | 严重度 | 应对 |
|---|---|---|
| 技术交付缺失（Elon 空输出） | 高 | 需立即补齐，阻塞整体进度 |
| 早期 Issue 无人响应 | 高 | GitHub Actions 自动标签 + 维护者轮值 |
| README 信息过载导致新用户流失 | 中 | Quick Start 严格控制 < 5 min，其余折叠或外链 |
| 单一渠道依赖（仅 GitHub） | 低 | 30 天后评估 PyPI 描述优化、awesome-list 等被动渠道 |

---

**下一步行动：请提供项目名称和核心功能描述，我会协调 Elon 立即生成全部模板文件，Henry 的增长计划同步落地。**
