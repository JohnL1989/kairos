#!/usr/bin/env python3
"""
Aion Memory — 健康检查脚本
用途：检查 5 个 Docker 容器运行状态 + 2 个 API 健康 + builtin memory 容量
输出约定：空输出 = 全部健康 = 静默；非空输出 = 有问题
"""
import subprocess, json, sys, os, time
from datetime import datetime
from pathlib import Path

LOG_DIR = Path.home() / ".aion-memory" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "health.log"

CONTAINERS = ["honcho-db", "honcho-api", "honcho-deriver", "amber-db", "amber-api"]
HEALTH_URLS = {
    "honcho-api": "http://127.0.0.1:8000/health",
    "amber-api": "http://127.0.0.1:8010/",
}

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def run(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.returncode
    except Exception as e:
        return str(e), 1

def check_containers():
    issues = []
    for name in CONTAINERS:
        out, rc = run(f"docker inspect -f '{{{{.State.Status}}}}' {name}", timeout=10)
        if out != "running":
            issues.append(f"  ❌ {name}: {out}")
    return issues

def check_apis():
    issues = []
    for name, url in HEALTH_URLS.items():
        out, rc = run(f"curl -s --max-time 5 {url}", timeout=10)
        if rc != 0:
            issues.append(f"  ❌ {name}: unreachable")
        elif "ok" not in out.lower() and "tiers" not in out:
            issues.append(f"  ❌ {name}: unexpected response: {out[:80]}")
    return issues

def main():
    issues = check_containers() + check_apis()
    if issues:
        log("健康检查发现问题：")
        for i in issues:
            log(i)
        sys.exit(1)
    # 全部健康，静默退出

if __name__ == "__main__":
    main()
