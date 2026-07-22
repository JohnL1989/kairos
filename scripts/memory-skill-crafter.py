"""
Aion Memory — 功淬为器（Skill Crafter）
从最近 30 天 cron 会话输出中自动识别可复用模板/规则，
输出结构化建议 → stdout（供 cron agent 执行 skill_manage）。

调用方式：cron 每周日 Layer 3 反思后执行
"""

import json, os, re, subprocess, sys
from datetime import datetime, timedelta
from pathlib import Path

LOG_DIR = Path.home() / ".aion-memory" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

SESSION_DIR = os.path.expanduser("~/AppData/Local/hermes/sessions")


def log(msg: str):
    ts = datetime.now().isoformat()
    print(f"[{ts}] {msg}", file=sys.stderr, flush=True)


def fetch_recent_sessions(days: int = 30) -> list:
    """获取最近 N 天的 cron session 文件"""
    sessions = []
    if not os.path.exists(SESSION_DIR):
        return sessions
    cutoff = datetime.now() - timedelta(days=days)
    for fname in os.listdir(SESSION_DIR):
        if fname.endswith('.json'):
            fpath = os.path.join(SESSION_DIR, fname)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                if mtime >= cutoff:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    sessions.append(data)
            except Exception:
                pass
    return sessions


def extract_patterns(sessions: list) -> list:
    """从会话中提取可复用模式"""
    patterns = []
    pattern_keywords = {
        "audit-workflow": ["审计", "修复", "验证", "全量测试"],
        "subagent-best-practices": ["子代理", "delegate_task", "429"],
        "windows-path-safety": ["MSYS2", "中文路径", "幻影"],
        "dual-track-development": ["双轨制", "v2", "隔离"],
        "release-discipline": ["git tag", "Release", "版本号"],
    }
    for session in sessions:
        messages = session.get("messages", [])
        text = " ".join(str(m.get("content", "")) for m in messages).lower()
        for skill_name, keywords in pattern_keywords.items():
            if all(kw.lower() in text for kw in keywords):
                patterns.append({
                    "skill": skill_name,
                    "trigger": "关键词匹配",
                    "confidence": 0.6,
                    "sample_messages": [m.get("content", "")[:100] for m in messages[:3] if m.get("role") == "user"][:2],
                })
    return patterns


def main():
    sessions = fetch_recent_sessions(30)
    if not sessions:
        print(json.dumps({"status": "no_sessions", "patterns": []}, ensure_ascii=False), flush=True)
        return
    patterns = extract_patterns(sessions)
    result = {
        "generated_at": datetime.now().isoformat(),
        "sessions_analyzed": len(sessions),
        "patterns_found": len(patterns),
        "patterns": patterns,
    }
    print(json.dumps(result, ensure_ascii=False), flush=True)
    log(f"功淬为器分析完成：{len(sessions)} 个会话 → {len(patterns)} 个模式")


if __name__ == "__main__":
    main()
