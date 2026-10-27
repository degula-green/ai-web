import asyncio
import os
import sys
from pathlib import Path
import json

# 配置路径
backend_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(backend_root))

from app.core.config import get_settings
from app.crawler.mediacrawler.sidecar import SignSrvSidecar
from app.crawler.mediacrawler.runner_entry import main as runner_main

async def run_full_stack_test():
    settings = get_settings()
    
    # 强制物理重定向
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("--- [1] 正在启动签名服务 (SignSrv Sidecar) ---")
    sidecar = SignSrvSidecar(settings=settings.media_crawler, logging_settings=settings.logging)
    try:
        await sidecar.ensure_started()
        print(f"签名服务已就绪: {sidecar.endpoint}")
        
        print("--- [2] 正在拉起爬虫内核 ---")
        job_spec_path = backend_root / "scratch" / "debug_job_spec.json"
        
        # 构造执行 runner_entry 的命令 (为了环境隔离，继续用 subprocess 启动 runner)
        import subprocess
        mc_root = backend_root / "agent-stack" / "crawler-engine"
        if not mc_root.exists():
            mc_root = backend_root / "agent-stack" / "MediaCrawlerPro-Python"

        cmd = [
            "uv", "run", "python", str(backend_root / "app" / "crawler" / "mediacrawler" / "runner_entry.py"),
            "--job-spec", str(job_spec_path),
            "--mc-root", str(mc_root)
        ]
        
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
        print(f"爬虫执行结束，码值: {process.returncode}")

    finally:
        print("--- [3] 正在关闭签名服务 ---")
        await sidecar.shutdown()

if __name__ == "__main__":
    asyncio.run(run_full_stack_test())
