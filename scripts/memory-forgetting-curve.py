"""
Aion Memory — 艾宾浩斯遗忘曲线 (Ebbinghaus Forgetting Curve)
触发方式：每日 cron (no_agent)，与 Layer 2 并行执行

原理：
  R = e^(-t/S) + 0.1
  R = 记忆保留率 (0-1)
  t = 距上次访问的天数
  S = 半衰期（默认 7 天，高强度记忆 14 天，低强度 3 天）

流程：
  1. 从 Mnemosyne 获取最近 30 天 memories
  2. 计算每条记忆的保留率 R
  3. R < 0.2 → 降级到 L3（低优先级，不召回）
  4. R < 0.05 → 标记遗忘（保留但不主动召回）
  5. 输出结构化 JSON → stdout
"""

import json
import os
import subprocess
import sys
import math
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

LOG_DIR = Path.home() / ".aion-memory" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

MNEMOSYNE_API = os.environ.get("MNEMOSYNE_API_URL", "http://127.0.0.1:8010")
HALF_LIFE_DAYS = float(os.environ.get("FORGETTING_HALF_LIFE", "7"))
RETENTION_THRESHOLD_DEGRADE = 0.2   # 降级到 L3
RETENTION_THRESHOLD_FORGET = 0.05   # 标记遗忘


def log(msg: str):
    ts = datetime.now().isoformat()
    print(f"[{ts}] {msg}", file=sys.stderr, flush=True)


def curl_get(url: str, timeout: int = 30) -> dict:
    try:
        r = subprocess.run(
            ["curl", "-s", "--max-time", str(timeout), url],
            capture_output=True, text=True, timeout=timeout + 5
        )
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
    except Exception as e:
        log(f"curl_get failed: {e}")
    return {}


def ebbinghaus_retention(days_elapsed: float, half_life: float = HALF_LIFE_DAYS) -> float:
    """艾宾浩斯保留率 R = e^(-t/S) + 0.1（最低保留 10%）"""
    return math.exp(-days_elapsed / half_life) + 0.1


APPLY = False


def _main_impl():
    # 1. 获取近期 memories
    since = (datetime.now() - timedelta(days=30)).isoformat()
    url = f"{MNEMOSYNE_API}/api/v1/memories?since={since}&limit=500"
    data = curl_get(url)
    memories = data.get("data", {}).get("memories", [])

    if not memories:
        print("{}", flush=True)
        return

    now = datetime.now()
    degraded = []
    forgotten = []
    stats = {"total": 0, "degraded": 0, "forgotten": 0, "retained": 0}

    for m in memories:
        created_at_str = m.get("created_at")
        if not created_at_str:
            continue
        try:
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        except ValueError:
            continue

        days_elapsed = (now - created_at).total_seconds() / 86400
        if days_elapsed < 0:
            continue

        retention = ebbinghaus_retention(days_elapsed)
        memory_id = m.get("id")
        content = m.get("content", "")[:80]

        if retention < RETENTION_THRESHOLD_FORGET:
            forgotten.append({"id": memory_id, "retention": round(retention, 3), "content": content})
            stats["forgotten"] += 1
        elif retention < RETENTION_THRESHOLD_DEGRADE:
            degraded.append({"id": memory_id, "retention": round(retention, 3), "content": content})
            stats["degraded"] += 1
        else:
            stats["retained"] += 1
        stats["total"] += 1

    result = {
        "generated_at": now.isoformat(),
        "half_life_days": HALF_LIFE_DAYS,
        "stats": stats,
        "degraded": degraded[:20],    # 最多 20 条
        "forgotten": forgotten[:20],
    }
    print(json.dumps(result, ensure_ascii=False), flush=True)
    log(f"遗忘曲线计算完成：{stats}")

    # P5 修复：--apply 模式将衰减回写。遗忘曲线本应影响 durable 记忆的热度，
    # 但原脚本只 print 不回写，衰减从未生效（且依赖易碎的 cron）。此处经内置
    # /api/v1/reflect?mode=light 端点触发时间衰减回写，使衰减闭环真正落地。
    if APPLY:
        try:
            req = urllib.request.Request(
                f"{MNEMOSYNE_API}/api/v1/reflect?mode=light",
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                apply_result = json.loads(resp.read())
            log(f"遗忘曲线衰减已回写（reflect）：{apply_result}")
        except Exception as e:
            log(f"遗忘曲线衰减回写失败：{e}")


def main():
    global APPLY
    parser = argparse.ArgumentParser(description="Aion Memory 艾宾浩斯遗忘曲线")
    parser.add_argument("--apply", action="store_true",
                        help="计算完成后经 /api/v1/reflect 回写衰减（而非仅打印）")
    args = parser.parse_args()
    APPLY = args.apply
    _main_impl()


if __name__ == "__main__":
    main()
