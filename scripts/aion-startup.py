#!/usr/bin/env python3
"""
Aion Memory — 系统启动编排
用途：电脑重启后自动编排所有记忆系统组件
设计：零干预，静默运行，失败时写日志
"""
import subprocess, time, json, os, sys
from datetime import datetime
from pathlib import Path

LOG_DIR = Path.home() / ".aion-memory" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "startup.log"
STATUS_FILE = LOG_DIR / "startup-status.json"

CONTAINERS = ["honcho-db", "honcho-api", "honcho-deriver", "amber-db", "amber-api"]
HEALTH_URLS = {
    "honcho-api": "http://127.0.0.1:8000/health",
    "amber-api": "http://127.0.0.1:8010/api/v1/health/default",
}

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT", 1
    except Exception as e:
        return str(e), 1

def wait_for_docker(max_wait=120):
    log("等待 Docker Desktop 就绪...")
    start = time.time()
    while time.time() - start < max_wait:
        out, rc = run("docker info", timeout=10)
        if rc == 0:
            log(f"Docker 就绪 ({int(time.time()-start)}s)")
            return True
        time.sleep(5)
    log(f"Docker 超时 ({max_wait}s)")
    return False

def ensure_containers():
    log("检查容器状态...")
    for name in CONTAINERS:
        out, rc = run(f'docker inspect -f "{{{{.State.Status}}}}" {name}', timeout=10)
        if out == "running":
            log(f"  {name}: ✅")
        elif out in ("exited", "created"):
            log(f"  {name}: ⚠️ {out} → 启动中...")
            run(f"docker start {name}", timeout=15)
            time.sleep(3)
        else:
            log(f"  {name}: ❌ {out}")

def health_check():
    log("健康检查...")
    results = {}
    for name, url in HEALTH_URLS.items():
        out, rc = run(f"curl -s --max-time 5 {url}", timeout=10)
        ok = rc == 0 and ("ok" in out.lower() or "tiers" in out)
        results[name] = ok
        log(f"  {name}: {'✅' if ok else '❌'}")
    return results

def main():
    log("=" * 50)
    log("Aion Memory 系统启动开始")
    
    docker_ok = wait_for_docker()
    if not docker_ok:
        log("❌ Docker 未就绪，退出")
        return
    
    ensure_containers()
    health = health_check()
    
    status = {
        "timestamp": datetime.now().isoformat(),
        "all_healthy": all(health.values()),
        "health": health,
    }
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)
    
    if status["all_healthy"]:
        log("✅ 全部组件正常运行")
    else:
        failed = [k for k, v in health.items() if not v]
        log(f"⚠️ 部分组件异常: {', '.join(failed)}")
    log("=" * 50)

if __name__ == "__main__":
    main()
