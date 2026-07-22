"""
Aion Memory — 规则自讼（skill 级别）
检查所有 skill 条目是否附带可预见的失效场景。
输出：JSON 格式，含违规条目列表和建议修正。

调用方式：memory-scripts-and-cron.md cron_self_audit_skill
"""

import json, os, re, sys
from datetime import datetime
from pathlib import Path

LOG_DIR = Path.home() / ".aion-memory" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str):
    ts = datetime.now().isoformat()
    print(f"[{ts}] {msg}", file=sys.stderr, flush=True)


def audit_soul() -> list:
    """审计 SOUL.md 中的规则"""
    soul_path = os.path.expanduser("~/AppData/Local/hermes/SOUL.md")
    if not os.path.exists(soul_path):
        return [{"file": "SOUL.md", "issue": "文件不存在", "severity": "error"}]
    with open(soul_path, 'r', encoding='utf-8') as f:
        content = f.read()
    issues = []
    # 检查元律 3：自讼预检（每条新规则需附带失效场景）
    if "失效场景" not in content:
        issues.append({"file": "SOUL.md", "issue": "元律 3 自讼预检未在 SOUL 中实施",
                        "severity": "warning", "fix": "在元律 3 中添加脚本自检"})
    return issues


def audit_instincts() -> list:
    """审计 memory/instinct 是否附带失效场景"""
    mem_path = os.path.expanduser("~/AppData/Local/hermes/memories/MEMORY.md")
    if not os.path.exists(mem_path):
        return [{"file": "MEMORY.md", "issue": "文件不存在", "severity": "error"}]
    with open(mem_path, 'r', encoding='utf-8') as f:
        content = f.read()
    issues = []
    # 扫描所有 instinct 块
    instinct_blocks = re.findall(r'§(.*?)(?=\n§|\Z)', content, re.DOTALL)
    for block in instinct_blocks:
        if 'confidence' in block and '失效场景' not in block:
            issues.append({"file": "MEMORY.md", "issue": f"instinct 未附带失效场景: {block[:60]}...",
                            "severity": "warning", "fix": "添加失效场景描述"})
    return issues


def audit_skills() -> list:
    """审计 Aion-Memory skills 是否附带失效场景"""
    skills_dir = os.path.join(os.path.expanduser("~/AppData/Local/hermes/skills"))
    if not os.path.exists(skills_dir):
        return []
    issues = []
    for skill_name in os.listdir(skills_dir):
        skill_md = os.path.join(skills_dir, skill_name, "SKILL.md")
        if not os.path.exists(skill_md):
            continue
        with open(skill_md, 'r', encoding='utf-8') as f:
            content = f.read()
        # 检查是否有失效场景描述
        if '失效' not in content and 'pifalls' not in content.lower() and 'edge' not in content.lower():
            issues.append({"file": f"skills/{skill_name}/SKILL.md",
                            "issue": "SKILL.md 未标注失效场景/边界条件",
                            "severity": "info", "fix": "添加失效场景或 pitfals 章节"})
    return issues


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "soul"
    if target == "soul":
        issues = audit_soul()
    elif target == "instinct":
        issues = audit_instincts()
    elif target == "skill":
        issues = audit_skills()
    else:
        issues = audit_soul() + audit_instincts() + audit_skills()
    result = {
        "audited_at": datetime.now().isoformat(),
        "target": target,
        "total_issues": len(issues),
        "issues": issues,
    }
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
