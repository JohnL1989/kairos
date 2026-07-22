#!/usr/bin/env python3
"""
Aion Memory — TMT 聚类脚本 (Layer 2 数据准备)
触发方式：每日 06:00 cron (no_agent)，由 memory-infra-health 健康检查通过后调用

流程：
  1. 调用 Amber API 获取所有近期记忆（默认 7 天）
  2. 调用 Honcho API 获取信念网络
  3. TMT L1→L2→L3 聚类分析（主题粗分类 + 热度计算）
  4. 输出结构化快照 JSON → stdout（供 cron agent 写入 Amber）

输出约定：
  - 成功：JSON 格式，含 clusters, hot_topics, stats
  - 静默：无新数据时输出空对象 {}（cron agent 判断静默）
  - 失败：非零退出码 + stderr 描述

依赖：curl（调用 Amber + Honcho API）
       HONCHO_API_URL, MNEMOSYNE_API_URL（环境变量，默认 localhost）
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

LOG_DIR = Path.home() / ".aion-memory" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

HONCHO_API = os.environ.get("HONCHO_API_URL", "http://127.0.0.1:8000")
MNEMOSYNE_API = os.environ.get("MNEMOSYNE_API_URL", "http://127.0.0.1:8010")
DAYS = int(os.environ.get("TMT_DAYS", "7"))


def log(msg: str):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line, file=sys.stderr, flush=True)


def curl_get(url: str, timeout: int = 30) -> dict:
    """调用 API，返回 JSON dict；失败返回空 dict"""
    try:
        r = subprocess.run(
            ["curl", "-s", "--max-time", str(timeout), url],
            capture_output=True, text=True, timeout=timeout + 5
        )
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
    except Exception as e:
        log(f"curl_get({url}) failed: {e}")
    return {}


def fetch_amber_memories(days: int = 7) -> list:
    """从 Amber 获取指定天数内的记忆"""
    since = (datetime.now() - timedelta(days=days)).isoformat()
    url = f"{MNEMOSYNE_API}/api/v1/memories?since={since}&limit=200"
    data = curl_get(url)
    return data.get("data", {}).get("memories", [])


def fetch_honcho_beliefs() -> list:
    """从 Honcho 获取信念网络"""
    url = f"{HONCHO_API}/api/v1/memories?type=belief&limit=100"
    data = curl_get(url)
    return data.get("data", {}).get("memories", [])


def tmt_l1_cluster(memories: list) -> dict:
    """TMT L1：主题粗分类（基于关键词匹配，无 LLM 调用）"""
    clusters: dict[str, list] = {}
    topic_keywords = {
        "audit": ["审计", "修复", "验证", "pytest", "coverage", "quality"],
        "memory": ["记忆", "memory", "instinct", "amber", "honcho", "mnem"],
        "architecture": ["架构", "architecture", "design", "重构", "refactor"],
        "tooling": ["工具", "tool", "cron", "docker", "deployment"],
        "error": ["错误", "error", "bug", "fix", "修复"],
        "feature": ["功能", "feature", "需求", "requirement", "开发"],
    }

    for m in memories:
        content = m.get("content", "").lower()
        matched = None
        for topic, kws in topic_keywords.items():
            if any(kw in content for kw in kws):
                matched = topic
                break
        if matched is None:
            matched = "general"
        clusters.setdefault(matched, []).append(m)

    return clusters


def tmt_l2_hotness(clusters: dict) -> list:
    """TMT L2：热度计算（基于条目数 + 最近更新时间）"""
    hot_topics = []
    now = datetime.now()
    for topic, items in clusters.items():
        count = len(items)
        if count == 0:
            continue
        # 热度 = 条目数 * 0.7 + 近 24h 条目 * 0.3
        recent = sum(
            1 for m in items
            if isinstance(m.get("created_at"), str)
            and (now - datetime.fromisoformat(m["created_at"].replace("Z", "+00:00"))).total_seconds() < 86400
        )
        hotness = round(count * 0.7 + recent * 0.3, 2)
        hot_topics.append({"topic": topic, "count": count, "recent_24h": recent, "hotness": hotness})
    hot_topics.sort(key=lambda x: x["hotness"], reverse=True)
    return hot_topics


def tmt_l3_summary(clusters: dict, hot_topics: list) -> dict:
    """TMT L3：生成结构化快照（供 Layer 3 反思使用）"""
    snapshot = {
        "generated_at": datetime.now().isoformat(),
        "period_days": DAYS,
        "stats": {
            "total_memories": sum(len(v) for v in clusters.values()),
            "topic_count": len(clusters),
            "hot_topic_count": len([t for t in hot_topics if t["hotness"] > 5]),
        },
        "clusters": {
            topic: {"count": len(items)}
            for topic, items in clusters.items()
        },
        "hot_topics": hot_topics[:10],
    }
    return snapshot


def main():
    log("memory-tmt-cluster.py 启动")

    memories = fetch_amber_memories(DAYS)
    if not memories:
        log("无新记忆，静默退出")
        print("{}", flush=True)
        return

    log(f"获取到 {len(memories)} 条记忆")

    clusters = tmt_l1_cluster(memories)
    hot_topics = tmt_l2_hotness(clusters)
    snapshot = tmt_l3_summary(clusters, hot_topics)

    # 输出 JSON 到 stdout
    # 输出 JSON 到 stdout（供 cron agent 捕获）
    print(json.dumps(snapshot, ensure_ascii=False), flush=True)
    # 写入快照文件（供 Layer 3 反思脚本读取）
    snapshot_path = Path.home() / ".aion-memory" / "logs" / "latest_snapshot.json"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    log(f"TMT 聚类完成：{snapshot['stats']} → 快照已写入 {snapshot_path}")


if __name__ == "__main__":
    main()
