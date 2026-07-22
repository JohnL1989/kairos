#!/usr/bin/env python3
"""Aion Memory — 合成检索基准测试（Recall Quality Benchmark）

测量 Mnemosyne API 在不同查询类型下的召回质量、延迟和退化行为。
输出 JSON 报告到 stdout，支持 --verbose 模式查看详情。

Usage:
    python scripts/benchmark.retrieval.py                      # 全量基准测试
    python scripts/benchmark.retrieval.py --dry-run            # 仅显示测试计划
    python scripts/benchmark.retrieval.py --verbose            # 详细输出（含匹配内容）
    python scripts/benchmark.retrieval.py --endpoint http://localhost:8010  # 自定义端点
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_ENDPOINT = "http://127.0.0.1:8010"

# ── 测试查询集 ──
# 格式：(category, query, min_hits, keywords)
#   category: 查询类别
#   query: 搜索关键词
#   min_hits: 至少应返回的结果数（0=不检查）
#   keywords: 期望结果中包含的关键词（空列表=不检查）
TEST_QUERIES: List[Tuple[str, str, int, List[str]]] = [
    # — 偏好类（应稳定召回 durable 记忆） —
    ("preference", "开源仓库 定位 拉取即用", 1, ["开源", "仓库", "克隆"]),
    ("preference", "Release 版本号 更新", 1, ["Release", "版本号"]),
    ("preference", "GitHub 发版 流程", 1, ["GitHub", "Release"]),
    ("preference", "决策 方案 A/B", 1, ["决策", "方案"]),

    # — 项目知识类 —
    ("project", "Hermes Memory Provider", 1, ["MemoryProvider"]),
    ("project", "Aion-Memory Mnemosyne", 1, ["Mnemosyne"]),
    ("project", "aion_* 工具 路由", 1, ["aion", "工具"]),

    # — 通用搜索（general 记忆） —
    ("general", "test memory", 1, ["test"]),
    ("general", "测试 记忆", 0, []),

    # — 边界/退化查询 —
    ("degenerate", "a", 0, []),                     # 单字符
    ("degenerate", "12345", 0, []),                  # 纯数字
    ("degenerate", "你好 hello hi", 0, []),          # 问候语
    ("degenerate", "", 0, []),                       # 空字符串
]


def _api_post(url: str, payload: dict, timeout: int = 10) -> Optional[dict]:
    """同步 POST 请求到 Mnemosyne API。"""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "detail": e.read().decode("utf-8", errors="replace")[:200]}
    except (urllib.error.URLError, OSError) as e:
        return {"error": f"Connection failed: {e}"}


def run_single_test(
    endpoint: str,
    category: str,
    query: str,
    min_hits: int,
    keywords: List[str],
    verbose: bool,
) -> Dict[str, Any]:
    """执行单条检索测试，返回测试结果字典。"""
    result: Dict[str, Any] = {
        "category": category,
        "query": query,
        "min_hits": min_hits,
        "keywords": keywords,
    }

    start = time.time()
    resp = _api_post(f"{endpoint}/api/v1/dialectic", {
        "query": query, "max_memories": 5, "user_id": "default",
    })
    elapsed = round((time.time() - start) * 1000, 1)  # ms

    result["latency_ms"] = elapsed

    if resp and "error" not in resp:
        memories = resp.get("data", {}).get("memories", [])
        hits = len(memories)
        result["hits"] = hits
        result["pass_hits"] = hits >= min_hits

        # 检查关键词召回
        matched_keywords = []
        all_content = " ".join(m.get("content", "") for m in memories)
        for kw in keywords:
            if kw.lower() in all_content.lower():
                matched_keywords.append(kw)
        result["matched_keywords"] = matched_keywords
        result["keyword_recall"] = len(matched_keywords) / max(len(keywords), 1)

        if verbose:
            result["_memories"] = [
                {"id": m.get("id"), "content": m.get("content", "")[:120],
                 "scope": m.get("scope", "?"), "score": m.get("score", 0)}
                for m in memories[:3]
            ]
    else:
        result["error"] = resp.get("error", "unknown") if resp else "no response"
        result["hits"] = 0
        result["pass_hits"] = False
        result["matched_keywords"] = []
        result["keyword_recall"] = 0.0

    return result


def print_report(results: List[Dict[str, Any]]) -> None:
    """打印人类可读的测试报告。"""
    categories = {}
    for r in results:
        categories.setdefault(r["category"], []).append(r)

    total = len(results)
    passed = sum(1 for r in results if r.get("pass_hits"))
    avg_latency = sum(r.get("latency_ms", 0) for r in results) / max(total, 1)

    print(f"╔══════════════════════════════════════════════╗")
    print(f"║   Aion Memory — 检索基准测试报告             ║")
    print(f"╚══════════════════════════════════════════════╝")
    print()
    total_keyword_count = sum(len(r.get("matched_keywords", [])) for r in results)
    total_keyword_possible = sum(len(r.get("keywords", [])) for r in results if not r.get("error"))
    keyword_recall = total_keyword_count / max(total_keyword_possible, 1)
    print(f"总用例:    {total}")
    print(f"通过:      {passed}/{total} ({passed/max(total,1)*100:.0f}%)")
    print(f"关键词召回率: {keyword_recall:.0%}")
    print(f"平均延迟:  {avg_latency:.0f}ms")
    print()

    for cat, tests in categories.items():
        cat_total = len(tests)
        cat_pass = sum(1 for t in tests if t.get("pass_hits"))
        cat_avg_lat = sum(t.get("latency_ms", 0) for t in tests) / max(cat_total, 1)
        status = "✅" if cat_pass == cat_total else "⚠️"
        print(f"  {status} [{cat}] {cat_pass}/{cat_total} passed, ∅{cat_avg_lat:.0f}ms")

        for t in tests:
            hit_ok = "✓" if t.get("pass_hits") else "✗"
            kw = t.get("matched_keywords", [])
            kw_str = f"keywords=[{','.join(kw)}]" if kw else "no-kw-check"
            err = f" ERROR={t.get('error')}" if t.get("error") else ""
            print(f"      {hit_ok} \"{t['query'][:40]}\" → {t.get('hits', 0)} hits "
                  f"({t.get('latency_ms', 0):.0f}ms) {kw_str}{err}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Aion Memory 合成检索基准测试")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="Mnemosyne API 地址")
    parser.add_argument("--dry-run", action="store_true", help="仅显示测试计划")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    # 健康检查
    try:
        req = urllib.request.Request(f"{args.endpoint}/api/v1/health/default")
        with urllib.request.urlopen(req, timeout=5) as resp:
            health = json.loads(resp.read())
    except Exception as e:
        print(f"❌ Mnemosyne API 不可达: {e}")
        sys.exit(1)

    if args.dry_run:
        print(f"🔍 Mnemosyne: {health.get('data', {}).get('service', '?')}")
        print(f"📋 测试计划: {len(TEST_QUERIES)} 条查询")
        cats = {}
        for cat, q, _, _ in TEST_QUERIES:
            cats.setdefault(cat, []).append(q)
        for cat, queries in cats.items():
            print(f"   [{cat}] {len(queries)} 条")
            for q in queries:
                print(f"       \"{q}\"")
        return

    print(f"🔍 Mnemosyne: {health.get('data', {}).get('service', '?')}")
    print(f"📊 运行 {len(TEST_QUERIES)} 条检索测试...")
    print()

    results: List[Dict[str, Any]] = []
    for i, (category, query, min_hits, keywords) in enumerate(TEST_QUERIES, 1):
        result = run_single_test(args.endpoint, category, query, min_hits, keywords, args.verbose)
        results.append(result)
        marker = "✓" if result.get("pass_hits") else "✗"
        print(f"  [{i:2d}/{len(TEST_QUERIES)}] {marker} [{category[:8]:>8}] "
              f"\"{query[:40]:<40}\" → {result.get('hits', 0)} hits "
              f"({result.get('latency_ms', 0):.0f}ms)", end="")
        if result.get("error"):
            print(f" [ERROR: {result['error']}]", end="")
        print()

    print()
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print_report(results)

    # Exit code: 失败数
    passed = sum(1 for r in results if r.get("pass_hits"))
    failed = len(results) - passed
    sys.exit(0 if failed == 0 else min(failed, 127))


if __name__ == "__main__":
    main()
