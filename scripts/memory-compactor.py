"""
记忆压缩器 v2.1 — 自动读写 MEMORY.md / USER.md，执行实际压缩
由每日 cron 05:00 调用（no_agent 模式），静默运行

阶段1: 删 [status]/[task_type] 条目（过期记录）
阶段2: 删 enforcement=soul 的 rule 条目（已在 SOUL 固化）
阶段3: 合并同 domain instinct（≥3条合为1条，保留最长）
阶段4: force_clean 时删最旧无标签条目

USER.md 仅执行阶段1（删 status/task_type），不做深度压缩
"""

import json, os, re, sys
from datetime import datetime
from pathlib import Path

MEMORY_PATH = Path.home() / "AppData/Local/hermes/memories/MEMORY.md"
USER_PATH = Path.home() / "AppData/Local/hermes/memories/USER.md"
MAX_SIZE = 20000
USER_MAX_SIZE = 10000

AUTO_COMPACT = 0.65
STOP_WRITE = 0.70
FORCE_CLEAN = 0.80


def log(msg: str):
    ts = datetime.now().isoformat()
    print(f"[{ts}] {msg}", file=sys.stderr, flush=True)


def parse_md(path: Path) -> tuple[list[dict], str]:
    if not path.exists():
        return [], ""
    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")
    header = lines[0].strip() if lines else ""
    remaining = "\n".join(lines[1:]) if len(lines) > 1 else ""
    
    raw_blocks = re.split(r'\n§(?:\n|$)', remaining)
    
    entries = []
    for block in raw_blocks:
        block = block.strip()
        if not block or block == "§":
            continue
        text = re.sub(r'^§\s*', '', block).strip()
        if not text:
            continue
        
        tags_raw = ""
        tags = {}
        m = re.match(r'^(\[[^\]]*\](?:\[[^\]]*\])*)', text)
        if m:
            tags_raw = m.group(1)
            text = text[m.end():].strip()
            for t in re.findall(r'\[([^\]]+)\]', tags_raw):
                parts = t.split(":")
                if len(parts) >= 2:
                    tags[parts[0].strip()] = ":".join(parts[1:]).strip()
                elif parts[0].strip() in ("instinct", "lesson", "rule", "error", "status", "skill", "task_type"):
                    tags["type"] = parts[0].strip()
                else:
                    tags.setdefault("domain", parts[0].strip())
        
        severity = None
        for word in ("critical", "high", "medium", "low"):
            if f"[{word}]" in tags_raw.lower():
                severity = word
                break
        
        enforcement = None
        em = re.search(r'enforcement:\s*(\S+)', text)
        if em:
            enforcement = em.group(1)
        
        since = None
        sm = re.search(r'since\s+(\d{4}-\d{2}-\d{2})', text)
        if sm:
            since = sm.group(1)
        
        confidence = 0.8
        cm = re.search(r'confidence:\s*(0\.\d+)', text)
        if cm:
            confidence = float(cm.group(1))
        
        entries.append({
            "raw": block,
            "type": tags.get("type", "fact"),
            "domain": tags.get("domain", "general"),
            "severity": severity,
            "enforcement": enforcement,
            "since": since,
            "confidence": confidence,
            "text": text,
            "length": len(block),
        })
    
    return entries, header


def write_md(path: Path, entries: list[dict], header: str) -> int:
    lines = [header]
    for e in entries:
        lines.append("")
        lines.append("§")
        lines.append(e["raw"])
    content = "\n".join(lines) + "\n"
    path.write_text(content, encoding="utf-8")
    return len(content.encode("utf-8"))


def compact_memory(entries: list[dict], pct: float, target_max: int, is_user: bool = False) -> tuple[list[dict], list[str]]:
    """执行压缩。is_user=True 时只做安全清理（删 status/task_type）"""
    kept = list(entries)
    logs = []
    
    action = "ok"
    if pct >= FORCE_CLEAN:
        action = "force_clean"
    elif pct >= STOP_WRITE:
        action = "stop_writes"
    elif pct >= AUTO_COMPACT:
        action = "auto_compact"
    
    if action == "ok":
        return kept, logs
    
    removed = set()
    
    # ── 阶段1: 安全删除（两个文件都适用）──
    for i, e in enumerate(entries):
        if i in removed:
            continue
        if e["type"] == "status":
            removed.add(i)
            logs.append(f"删status: {e['text'][:60]}")
        elif e["type"] == "task_type":
            removed.add(i)
            logs.append(f"删task_type: {e['text'][:60]}")
    
    # ── USER.md: 只做阶段1 ──
    if is_user:
        return [e for i, e in enumerate(entries) if i not in removed], logs
    
    # ── MEMORY.md 额外规则 ──
    for i, e in enumerate(entries):
        if i in removed:
            continue
        # 阶段2: enforcement=soul 且是 rule
        if e["enforcement"] == "soul" and e["type"] in ("rule",):
            removed.add(i)
            logs.append(f"删soul-rule: {e['text'][:60]}")
        # 低置信度
        elif e["confidence"] < 0.3 and e["type"] != "instinct":
            removed.add(i)
            logs.append(f"删低置信({e['confidence']:.1f}): {e['text'][:50]}")
        # 过短 (<40字符) 非 instinct/skill/lesson
        elif len(e["text"]) < 40 and e["type"] not in ("instinct", "skill", "lesson") and e["confidence"] < 0.6:
            removed.add(i)
            logs.append(f"删过短({len(e['text'])}字): {e['text'][:40]}")
    
    kept = [e for i, e in enumerate(entries) if i not in removed]
    
    # ── 阶段3: 合并同 domain instinct（≥3条→1条）──
    instinct_domains = {}
    for i, e in enumerate(kept):
        if e["type"] == "instinct":
            instinct_domains.setdefault(e["domain"], []).append(i)
    
    merge_indices = set()
    for domain, indices in instinct_domains.items():
        if len(indices) >= 3:
            # 保留最长（信息量最大）
            best = max(indices, key=lambda i: len(kept[i]["text"]))
            for idx in indices:
                if idx != best:
                    merge_indices.add(idx)
            logs.append(f"合 instinct {domain}: {len(indices)}条→1条")
    
    kept = [e for i, e in enumerate(kept) if i not in merge_indices]
    
    # ── 阶段4: force_clean — 删除最旧可删条目 ──
    if action == "force_clean":
        current_text = "\n".join(["h"] + [e["raw"] for e in kept])
        current_size = len(current_text.encode("utf-8"))
        if current_size > target_max * 0.70:
            # 按可删性排序：fact/general 优先删，按长度（短优先）+ 无since优先
            removable = [e for e in kept if e["type"] not in ("instinct", "skill")]
            removable.sort(key=lambda e: (
                0 if e["since"] is None else 1,
                e["since"] or "0000-00-00",
                e["length"],
            ))
            for e in removable:
                if current_size <= target_max * 0.70:
                    break
                kept.remove(e)
                current_text = "\n".join(["h"] + [e2["raw"] for e2 in kept])
                current_size = len(current_text.encode("utf-8"))
                logs.append(f"强制GC: {e['type']}/{e['domain']}: {e['text'][:50]}")
    
    return kept, logs


def main():
    memory_start = MEMORY_PATH.stat().st_size if MEMORY_PATH.exists() else 0
    user_start = USER_PATH.stat().st_size if USER_PATH.exists() else 0
    
    memory_pct = memory_start / MAX_SIZE
    user_pct = user_start / USER_MAX_SIZE
    
    result = {
        "status": "ready", "changes": False,
        "memory": {"size": memory_start, "pct": round(memory_pct * 100), "entries": 0},
        "user": {"size": user_start, "pct": round(user_pct * 100), "entries": 0},
        "logs": [],
    }
    
    # ── MEMORY.md ──
    if memory_pct >= AUTO_COMPACT and memory_start > 0:
        entries, header = parse_md(MEMORY_PATH)
        result["memory"]["entries"] = len(entries)
        if entries:
            kept, logs = compact_memory(entries, memory_pct, MAX_SIZE, is_user=False)
            if len(kept) < len(entries):
                written = write_md(MEMORY_PATH, kept, header)
                result["memory"]["size"] = written
                result["memory"]["pct"] = round(written / MAX_SIZE * 100)
                result["changes"] = True
                result["status"] = "compacted"
                result["logs"].extend(logs)
                log(f"MEMORY: {memory_start}→{written}B ({len(entries)}→{len(kept)}条)")
    
    # ── USER.md（只做安全清理）──
    if user_pct >= AUTO_COMPACT and user_start > 0:
        entries, header = parse_md(USER_PATH)
        result["user"]["entries"] = len(entries)
        if entries:
            kept, logs = compact_memory(entries, user_pct, USER_MAX_SIZE, is_user=True)
            if len(kept) < len(entries):
                written = write_md(USER_PATH, kept, header)
                result["user"]["size"] = written
                result["user"]["pct"] = round(written / USER_MAX_SIZE * 100)
                result["changes"] = True
                result["status"] = "compacted"
                result["logs"].extend(logs)
                log(f"USER: {user_start}→{written}B ({len(entries)}→{len(kept)}条)")
    
    # 静默：无操作时只输出状态，不输出日志
    if not result["changes"] and result["status"] == "ready":
        result["logs"] = []
    
    print(json.dumps(result, ensure_ascii=False))
    for msg in result["logs"]:
        log(msg)


if __name__ == "__main__":
    main()
