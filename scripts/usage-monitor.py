"""
使用率监控 — 每周统计 API 端点调用次数，标记零调用组件为弃用候选
由每周 cron 调用（no_agent 模式），静默输出

输出约定：
- 空/仅状态 = 健康 = cron 静默
- 非空 = 发现了零调用端点 = 输出 JSON 报告
"""

import json, os, sys
from datetime import date, datetime
from pathlib import Path

# ── 配置 ──
MNEMOSYNE_URL = os.getenv("MNEMOSYNE_URL", "http://127.0.0.1:8010")
API_KEY = os.getenv("MNEMOSYNE_API_KEY", "")
REPORT_DIR = Path.home() / ".aion-memory"

# 已知的全部端点清单（用于检测未注册调用记录的端点）
KNOWN_ENDPOINTS = {
    "GET /api/v1/memories": "记忆检索",
    "POST /api/v1/memories": "记忆写入",
    "DELETE /api/v1/memories/{id}": "记忆删除",
    "GET /api/v1/search": "记忆搜索",
    "POST /api/v1/reflect": "反思触发",
    "GET /api/v1/prefetch": "预取召回",
    "GET /api/v1/console/stats": "控制台统计",
    "GET /api/v1/console/maturity": "控制台成熟度",
    "GET /api/v1/wiki/{slug}": "Wiki 页面读取",
    "POST /api/v1/wiki": "Wiki 页面创建",
    "hermes_provider.store": "Hermes 记忆写入桥接",
    "hermes_provider.search": "Hermes 记忆搜索桥接",
    "hermes_provider.prefetch": "Hermes 预取桥接",
}
ZERO_CALL_THRESHOLD_WEEKS = 4  # 连续 4 周零调用 → 弃用候选


def log(msg: str):
    ts = datetime.now().isoformat()
    print(f"[{ts}] {msg}", file=sys.stderr, flush=True)


def fetch_usage_stats() -> dict:
    """从 Mnemosyne 获取使用率数据"""
    import urllib.request
    import urllib.error

    url = f"{MNEMOSYNE_URL}/api/v1/usage-stats"
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log(f"usage-stats API 不可用（可能未实现统计中间件）: {e}")
        return {}


def analyze(endpoint_stats: dict) -> dict:
    """分析使用率数据，标记零调用端点"""
    today = date.today()
    current_week = today.isocalendar()[1]

    # 整理已知端点状态
    zero_call = []
    active = []
    unknown = []

    for ep, desc in KNOWN_ENDPOINTS.items():
        stats = endpoint_stats.get(ep, {})
        total = stats.get("total_calls", 0)
        last_week = stats.get("last_week_calls", 0)

        entry = {
            "endpoint": ep,
            "description": desc,
            "total_calls": total,
            "last_week_calls": last_week,
        }

        if total == 0:
            zero_call.append(entry)
        else:
            entry["weeks_since_last_call"] = stats.get("weeks_since_last_call", 0)
            active.append(entry)

    # 连续 4 周零调用 → 弃用候选
    discard_candidates = [
        ep for ep in zero_call
        if KNOWN_ENDPOINTS.get(ep["endpoint"], "") != "预取召回"  # prefetch 正常情况较低
    ]

    return {
        "report_date": today.isoformat(),
        "week": current_week,
        "total_endpoints": len(KNOWN_ENDPOINTS),
        "active": len(active),
        "zero_call": len(zero_call),
        "zero_call_endpoints": zero_call,
        "discard_candidates": len(discard_candidates),
        "discard_candidate_endpoints": [e["endpoint"] for e in discard_candidates],
    }


def main():
    endpoint_stats = fetch_usage_stats()
    report = analyze(endpoint_stats)

    # 写入报告文件
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"usage-report-week-{report['week']}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # 输出：
    # - 有弃用候选 → 输出 JSON（非静默）
    # - 全部健康 → 静默
    if report["discard_candidates"] > 0:
        print(json.dumps(report, ensure_ascii=False))
        log(f"发现 {report['discard_candidates']} 个弃用候选端点")
    else:
        # 静默输出
        log(f"使用率健康: {report['active']}/{report['total_endpoints']} 活跃")


if __name__ == "__main__":
    main()
