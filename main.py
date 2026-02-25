from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime

# Fix Windows GBK encoding for both stdin and stdout
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")

from base_agent import get_timeline, reset_timeline
from echo import Echo


def _split_files(result: str) -> dict[str, str]:
    """Parse '=== FILE: name ===' delimiters into separate file contents."""
    files: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []

    for line in result.splitlines():
        stripped = line.strip()
        if stripped.startswith("=== FILE:") and stripped.endswith("==="):
            if current_name is not None:
                files[current_name] = "\n".join(current_lines).strip()
            current_name = stripped[9:-3].strip()
            current_lines = []
        else:
            if current_name is not None:
                current_lines.append(line)

    if current_name is not None:
        files[current_name] = "\n".join(current_lines).strip()

    return files


def _write_outputs(human_input: str, result: str, run_dir: str) -> None:
    os.makedirs(run_dir, exist_ok=True)

    # Try to split into named files; fall back to single result.md
    files = _split_files(result)
    if files:
        for filename, content in files.items():
            # Support subdirectories like .github/ISSUE_TEMPLATE/bug_report.yml
            filepath = os.path.join(run_dir, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content + "\n")
        print(f"[输出] 已保存 {len(files)} 个文件到 {run_dir}/")
    else:
        with open(os.path.join(run_dir, "result.md"), "w", encoding="utf-8") as f:
            f.write(f"# 任务输出\n\n**输入**: {human_input}\n\n---\n\n{result}\n")
        print(f"[输出] result.md 已保存到 {run_dir}/")

    # Always write timeline and original task
    timeline = get_timeline()
    lines = [
        "# Hive Mind 行动时间线\n",
        f"**任务**: {human_input}\n",
        f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        "\n| 耗时(s) | Agent | 事件 | 备注 |\n",
        "|---------|-------|------|------|\n",
    ]
    for e in timeline:
        detail = e["detail"].replace("|", "\\|") if e["detail"] else ""
        lines.append(f"| +{e['t']} | {e['agent']} | {e['event']} | {detail} |\n")
    with open(os.path.join(run_dir, "timeline.md"), "w", encoding="utf-8") as f:
        f.writelines(lines)
    with open(os.path.join(run_dir, "task.txt"), "w", encoding="utf-8") as f:
        f.write(human_input)


async def _run_once(echo: Echo, human_input: str) -> None:
    reset_timeline()
    result = await echo.coordinate(human_input)
    print(f"\nEcho > {result}\n")
    run_dir = os.path.join("outputs", datetime.now().strftime("%Y%m%d_%H%M%S"))
    _write_outputs(human_input, result, run_dir)


def _load_prior_output(prior_dir: str) -> dict[str, str]:
    """Recursively read all output files, skipping metadata."""
    skip = {"timeline.md", "task.txt"}
    files: dict[str, str] = {}
    for root, _, filenames in os.walk(prior_dir):
        for fname in filenames:
            if fname in skip:
                continue
            abs_path = os.path.join(root, fname)
            rel_path = os.path.relpath(abs_path, prior_dir).replace("\\", "/")
            with open(abs_path, encoding="utf-8") as f:
                files[rel_path] = f.read()
    return files


def _build_refine_prompt(prior_files: dict[str, str], original_task: str, feedback: str) -> str:
    parts = [
        "以下是团队上一轮的输出成果，请在保留优点的基础上，根据改进反馈重新输出全部文件。",
        "每个文件用 === FILE: 文件名 === 作为分隔符开头，不要省略任何文件。",
        "",
        f"原始任务：\n{original_task}" if original_task else "",
        f"\n改进反馈：\n{feedback}" if feedback else "\n改进反馈：（无具体反馈，请自行审视并优化）",
        "\n上一轮产出：",
    ]
    for filename, content in prior_files.items():
        parts.append(f"\n=== FILE: {filename} ===\n{content}")
    return "\n".join(p for p in parts if p is not None)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Hive Mind — multi-agent coordinator")
    parser.add_argument("--task", "-t", type=str, default=None,
                        help="Run a single task non-interactively and exit")
    parser.add_argument("--refine", type=str, default=None,
                        help="Path to prior output dir to refine")
    parser.add_argument("--feedback", type=str, default="",
                        help="Specific improvement feedback for --refine mode")
    args = parser.parse_args()

    echo = Echo()

    if args.task:
        print(f"[Hive Mind] 无人值守模式，任务: {args.task}")
        await _run_once(echo, args.task)
        return

    if args.refine:
        prior_files = _load_prior_output(args.refine)
        task_file = os.path.join(args.refine, "task.txt")
        original_task = open(task_file, encoding="utf-8").read().strip() if os.path.exists(task_file) else ""
        refine_prompt = _build_refine_prompt(prior_files, original_task, args.feedback)
        print(f"[Hive Mind] Refine 模式，基于: {args.refine}，载入 {len(prior_files)} 个文件")
        await _run_once(echo, refine_prompt)
        return

    # Interactive REPL
    print("Hive Mind 已启动。输入你的战略目标：")
    while True:
        human_input = input("Human > ").strip()
        if human_input.lower() in ("exit", "quit"):
            print("Hive Mind 已退出。")
            break
        if not human_input:
            continue
        await _run_once(echo, human_input)


if __name__ == "__main__":
    asyncio.run(main())
