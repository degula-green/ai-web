import subprocess
import os
import sys
from pathlib import Path

# 定义基础路径
backend_root = Path(__file__).parent.parent.resolve()
mc_root = backend_root / "agent-stack" / "crawler-engine"
if not mc_root.exists():
    mc_root = backend_root / "agent-stack" / "MediaCrawlerPro-Python"
runner_script = backend_root / "app" / "crawler" / "mediacrawler" / "runner_entry.py"
job_spec = backend_root / "scratch" / "debug_job_spec.json"

print(f"Backend Root: {backend_root}")
print(f"MC Root: {mc_root}")
print(f"Runner Script: {runner_script}")

# 检查路径是否存在
for p in [mc_root, runner_script, job_spec]:
    if not p.exists():
        print(f"ERROR: Path {p} does not exist!")
        sys.exit(1)

# 构造执行命令
# 使用 uv run python 确保环境一致
cmd = [
    "uv", "run", "python", str(runner_script),
    "--job-spec", str(job_spec),
    "--mc-root", str(mc_root)
]

print(f"Executing: {' '.join(cmd)}")

try:
    # 实时通过 stdout 查看到底跑没跑起来
    # 强制让当前脚本的 stdout 也能处理非法字符，防止 print 崩溃
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    process = subprocess.Popen(
        cmd,
        cwd=str(backend_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    for line in process.stdout:
        print(f"[CRAWLER]: {line.strip()}")

    process.wait()
    print(f"Process finished with exit code: {process.returncode}")

except Exception as e:
    print(f"Execution failed: {e}")
