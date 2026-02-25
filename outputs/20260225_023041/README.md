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

### 从 stdin 读取（管道用法）

snaplog 完整支持从标准输入（stdin）读取日志，方便与其他命令组合使用。将文件参数指定为 `-` 或直接省略文件参数即可从 stdin 读取。

```bash
# 使用管道将其他命令的输出传给 snaplog
cat /var/log/app.log | snaplog filter --level ERROR -

# 使用输入重定向
snaplog stats - < /var/log/app.log

# 与 grep / tail / zcat 等工具组合
tail -n 10000 app.log | snaplog stats -
zcat app.log.gz | snaplog filter --level WARNING -
grep "api-gateway" combined.log | snaplog stats -

# 多阶段管道：先过滤再统计
cat app.log | snaplog filter --level ERROR - | snaplog stats -

# 多阶段管道：先过滤再导出
cat app.log | snaplog filter --level ERROR - | snaplog export --format json --output errors.json -

# 从远程服务器实时拉取日志并分析
ssh prod-server "cat /var/log/app.log" | snaplog stats -

# 使用 kubectl 分析容器日志
kubectl logs my-pod | snaplog filter --level ERROR -
```

> **提示：** 当 snaplog 检测到 stdin 不是终端（即存在管道输入）时，会自动从 stdin 读取，此时 `-` 参数可省略。但为了脚本可读性，建议显式写 `-`。

> **Windows 用户注意：** 在 PowerShell 中管道行为与 Unix shell 略有不同。建议使用 `Get-Content app.log | snaplog filter --level ERROR -` 替代 `cat`，或在 WSL 环境下使用。

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
