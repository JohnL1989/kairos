#!/usr/bin/env python3
"""
Aion Memory — Layer 3 自主思考脚本
触发方式：每周日 18:00 cron (agent-mode)

流程：
  1. 读取 TMT 今日快照（memory-tmt-cluster.py 的输出或 Mnemosyne 中最近快照）
  2. 调用 LLM 进行三轮推理：模式发现 → 矛盾检测 → 缺口识别
  3. 输出反思报告 JSON → stdout

输出约定：
  - 成功：JSON 格式，含 patterns, contradictions, gaps, report
  - 静默：无快照数据时输出空对象 {}
  - 失败：非零退出码 + stderr 描述

依赖：curl（调用 LLM API + Mnemosyne API）
      LLM_API_URL, LLM_API_KEY（环境变量）
      HONCHO_API_URL, MNEMOSYNE_API_URL（环境变量）
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

LOG_DIR = Path.home() / ".aion-memory" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LLM_API = os.environ.get("LLM_API_URL", "http://127.0.0.1:8000/v1/chat/completions")
LLM_KEY = os.environ.get("LLM_API_KEY", "")
HONCHO_API = os.environ.get("HONCHO_API_URL", "http://127.0.0.1:8000")  # 预留：Honcho 集成后启用
MNEMOSYNE_API = os.environ.get("MNEMOSYNE_API_URL", "http://127.0.0.1:8010")


def log(msg: str):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line, file=sys.stderr, flush=True)


def curl_post(url: str, body: dict, timeout: int = 120) -> dict:
    """调用 LLM API，返回 JSON dict"""
    headers = ["-H", "Content-Type: application/json"]
    if LLM_KEY:
        headers += ["-H", f"Authorization: Bearer {LLM_KEY}"]
    try:
        r = subprocess.run(
            ["curl", "-s", "--max-time", str(timeout),
             "-X", "POST", *headers, "-d", json.dumps(body), url],
            capture_output=True, text=True, timeout=timeout + 5
        )
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
    except Exception as e:
        log(f"curl_post({url}) failed: {e}")
    return {}


def fetch_latest_snapshot() -> dict:
    """获取最新的 TMT 快照（优先读 memory-tmt-cluster.py 的输出文件）"""
    # 优先：从 TMT 聚类脚本的输出文件读取
    snapshot_path = Path.home() / ".aion-memory" / "logs" / "latest_snapshot.json"
    if snapshot_path.exists():
        with open(snapshot_path, encoding="utf-8") as f:
            return json.load(f)

    # 降级：从 Mnemosyne 获取 durable 记忆，现场构建简易快照
    url = f"{MNEMOSYNE_API}/api/v1/memories?scope=durable&since={(datetime.now() - timedelta(days=7)).isoformat()}&limit=200"
    data = curl_get(url)
    memories = data.get("data", {}).get("memories", [])
    if memories:
        total = len(memories)
        categories = {}
        for m in memories:
            cat = m.get("category", "general")
            categories[cat] = categories.get(cat, 0) + 1
        return {
            "generated_at": datetime.now().isoformat(),
            "period_days": 7,
            "stats": {"total_memories": total, "topic_count": len(categories)},
            "clusters": categories,
            "hot_topics": [{"topic": k, "count": v, "hotness": round(v * 0.7, 2)} 
                          for k, v in sorted(categories.items(), key=lambda x: -x[1])[:5]],
            "source": "fallback_live_fetch"
        }
    return {}


def curl_get(url: str, timeout: int = 30) -> dict:
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


def build_reflect_prompt(snapshot: dict) -> str:
    """构建三层推理 prompt"""
    topics = json.dumps(snapshot.get("hot_topics", [])[:5], ensure_ascii=False, indent=2)
    clusters = json.dumps(snapshot.get("clusters", {}), ensure_ascii=False, indent=2)

    return f"""你是一个记忆系统反思引擎。根据以下快照数据，完成三轮推理。

## 本周快照数据
- 时间窗口：{snapshot.get('period_days', 7)} 天
- 总记忆数：{snapshot.get('stats', {}).get('total_memories', 0)}
- 主题数：{snapshot.get('stats', {}).get('topic_count', 0)}

### 热点主题
{topics}

### 主题分布
{clusters}

## 三轮推理

### 1. 模式发现
提取 2-3 个值得关注的模式（如：某个主题持续高热度、跨会话重复出现的修复模式、用户行为变化）。

### 2. 矛盾检测
检查信念之间是否有冲突，或信念与近期记忆是否不匹配（如：某个被多次纠正的模式仍高置信度）。

### 3. 缺口识别
识别高频主题但没有信念覆盖的区域，或系统"不知道什么"的知识盲区。

## 输出格式
严格 JSON，不含 markdown：
{{
  "patterns": [{{"topic": "...", "observation": "...", "confidence": 0.0-1.0}}],
  "contradictions": [{{"belief_a": "...", "belief_b": "...", "conflict": "..."}}],
  "gaps": [{{"topic": "...", "missing": "...", "priority": "high/medium/low"}}],
  "report": "≤200字中文反思摘要"
}}
"""


def main():
    log("memory-layer3-reflect.py 启动")

    snapshot = fetch_latest_snapshot()
    if not snapshot:
        log("无快照数据，静默退出")
        print("{}", flush=True)
        return

    log(f"读取快照：{snapshot.get('stats', {})}")

    prompt = build_reflect_prompt(snapshot)

    body = {
        "model": os.environ.get("LLM_MODEL", "default"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 2048,
    }

    resp = curl_post(LLM_API, body, timeout=120)
    if not resp:
        log("LLM 不可用（无 API Key 或网络不通），静默退出")
        print("{}", flush=True)
        return

    # LLM 返回空内容 = 无 LLM 或调用失败 → 静默退出（降级路径）
    if not resp.get("choices"):
        log("LLM 不可用或返回空，静默退出")
        print("{}", flush=True)
        return
    content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        log("LLM 返回空内容，静默退出")
        print("{}", flush=True)
        return

    # 解析 LLM 返回的 JSON
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        # 如果 LLM 没有返回纯 JSON，尝试提取
        log("LLM 返回非 JSON，尝试提取")
        result = {"report": content[:500], "patterns": [], "contradictions": [], "gaps": []}

    result["generated_at"] = datetime.now().isoformat()
    result["source_snapshot"] = snapshot.get("stats", {})

    print(json.dumps(result, ensure_ascii=False), flush=True)
    log(f"Layer 3 反思完成：patterns={len(result.get('patterns', []))} "
        f"gaps={len(result.get('gaps', []))}")

    # ── 反馈验证环 ──
    # 1. 写入周报（追加到 dist/daily_report.md）
    report_path = Path.home() / ".aion-memory" / "logs" / "weekly_reflection.md"
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "a", encoding="utf-8") as f:
            f.write(f"## {datetime.now().strftime('%Y-%m-%d %H:%M')} Layer 3 反思\n\n")
            f.write(f"### 模式发现 ({len(result.get('patterns', []))} 条)\n")
            for p in result.get("patterns", []):
                f.write(f"- [{p.get('topic', '?')}] {p.get('observation', '')} (置信度 {p.get('confidence', 0):.0%})\n")
            f.write(f"\n### 矛盾 ({len(result.get('contradictions', []))} 条)\n")
            for c in result.get("contradictions", []):
                f.write(f"- {c.get('belief_a', '?')} ↔ {c.get('belief_b', '?')}: {c.get('conflict', '')}\n")
            f.write(f"\n### 知识缺口 ({len(result.get('gaps', []))} 条)\n")
            for g in result.get("gaps", []):
                f.write(f"- [{g.get('priority', '?')}] {g.get('topic', '?')}: {g.get('missing', '')}\n")
            f.write(f"\n> {result.get('report', '')}\n\n---\n\n")
        log(f"周报已写入 {report_path}")
    except Exception as e:
        log(f"周报写入失败: {e}")


if __name__ == "__main__":
    main()
