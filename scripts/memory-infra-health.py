#!/usr/bin/env python3
"""记忆系统健康检查 — 完整版
输出约定：空输出=健康=静默 | 非空=有问题=发送告警

层级：
  [INFRA]  基础设施层 — Docker/API/端口
  [VAULT]  知识库层   — Obsidian/SOUL同步
  [MEMORY] 记忆层     — capacity/质量
  [PIPE]   数据管道层 — TMT蒸馏/归档/回流
"""
import os, subprocess, sys, time, json, glob
from pathlib import Path
from datetime import datetime, timedelta

issues = []

def curl_get(url, timeout=5):
    """Simple curl GET, returns (body, ok)"""
    try:
        ret = subprocess.run(
            ["curl", "-s", "--max-time", str(timeout), url],
            capture_output=True, text=True, timeout=timeout + 5
        )
        return ret.stdout.strip(), ret.returncode == 0
    except Exception:
        return "", False

def curl_post_json(url, data, timeout=5):
    """Simple curl POST with JSON body"""
    try:
        ret = subprocess.run(
            ["curl", "-s", "--max-time", str(timeout),
             "-X", "POST", url,
             "-H", "Content-Type: application/json",
             "-d", json.dumps(data)],
            capture_output=True, text=True, timeout=timeout + 5
        )
        return ret.stdout.strip(), ret.returncode == 0
    except Exception:
        return "", False

def file_age_hours(path):
    """Return file age in hours, or -1 if not found"""
    try:
        mtime = os.path.getmtime(path)
        return (time.time() - mtime) / 3600
    except Exception:
        return -1

def file_size_kb(path):
    """Return file size in KB, or -1 if not found"""
    try:
        return os.path.getsize(path) / 1024
    except Exception:
        return -1

# ═══════════════════════════════════════════════════
# [INFRA] 基础设施层
# ═══════════════════════════════════════════════════

# ── 1. Docker daemon ──
ret = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=10)
if ret.returncode != 0:
    issues.append("❌ [INFRA] Docker daemon 未运行")
    # Docker down = everything downstream is unreachable, report and exit early
    print("🏥 记忆系统健康报告\n" + "\n".join(issues))
    sys.exit(0)

# ── 2. 容器状态（自动重启）──
for svc in ["honcho-db", "honcho-api", "amber-db", "amber-api"]:
    ret = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Status}}", svc],
        capture_output=True, text=True, timeout=10
    )
    status = ret.stdout.strip()
    if status != "running":
        subprocess.run(["docker", "start", svc], capture_output=True, timeout=10)
        time.sleep(3)
        ret2 = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Status}}", svc],
            capture_output=True, text=True, timeout=10
        )
        status2 = ret2.stdout.strip()
        if status2 != "running":
            issues.append(f"❌ [INFRA] {svc} 容器异常({status2})，自动重启失败")
        else:
            issues.append(f"⚠️ [INFRA] {svc} 已自动重启恢复")

# ── 2b. honcho-deriver 存活检查 ──
ret_deriver = subprocess.run(
    ["docker", "inspect", "-f", "{{.State.Status}}", "honcho-deriver"],
    capture_output=True, text=True, timeout=10
)
deriver_status = ret_deriver.stdout.strip()
if deriver_status != "running":
    subprocess.run(["docker", "start", "honcho-deriver"], capture_output=True, timeout=10)
    time.sleep(3)
    ret2 = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Status}}", "honcho-deriver"],
        capture_output=True, text=True, timeout=10
    )
    if ret2.stdout.strip() != "running":
        issues.append("❌ [INFRA] honcho-deriver 未运行 — Honcho 结论提炼停止（消息照存但不提炼）")
    else:
        issues.append("⚠️ [INFRA] honcho-deriver 已自动重启恢复")


# ── 3. llama-server ──
body, ok = curl_get("http://127.0.0.1:8080/v1/models")
if not ok:
    issues.append("❌ [INFRA] llama-server :8080 不可达")

# ── 4. Honcho API ──
body, ok = curl_get("http://127.0.0.1:8000/health")
if not ok or ("ok" not in body.lower() and "status" not in body.lower()):
    issues.append("❌ [INFRA] Honcho API :8000 异常")

# ── 5. Amber API ──
body, ok = curl_get("http://127.0.0.1:8010/")
if not ok:
    issues.append("❌ [INFRA] Amber API :8010 不可达")

# ── 6. Amber DB 数据新鲜度 ──
try:
    ret = subprocess.run(
        ["docker", "exec", "amber-db", "psql", "-U", "postgres", "-d", "amber",
         "-t", "-c", "SELECT COUNT(*) FROM memories WHERE created_at > NOW() - INTERVAL '24 hours'"],
        capture_output=True, text=True, timeout=10
    )
    count = ret.stdout.strip()
    if count.isdigit() and int(count) == 0:
        issues.append("⚠️ [INFRA] Amber 24h 无新记忆")
except Exception:
    pass

# ── 7. Honcho DB 数据新鲜度 ──
try:
    ret = subprocess.run(
        ["docker", "exec", "honcho-db", "psql", "-U", "postgres", "-d", "honcho",
         "-t", "-c", "SELECT COUNT(*) FROM messages WHERE created_at > NOW() - INTERVAL '24 hours'"],
        capture_output=True, text=True, timeout=10
    )
    count = ret.stdout.strip()
    if count.isdigit() and int(count) == 0:
        issues.append("⚠️ [INFRA] Honcho 24h 无新消息")
except Exception:
    pass

# ═══════════════════════════════════════════════════
# [VAULT] 知识库层
# ═══════════════════════════════════════════════════

HERMES_HOME = os.path.expanduser("~/AppData/Local/hermes")
VAULT_MAIN = "D:/知识库/Hermes记忆"
VAULT_LINK = "D:/知识库/工作台/55_知识引用/Hermes记忆"
SOUL_INTERNAL = os.path.join(HERMES_HOME, "SOUL.md")
SOUL_VAULT = "D:/知识库/工作台/99_库管理/Hermes配置/SOUL.md"

# ── 10b. Vault Doctor 快速健康检查（新增）──
try:
    vd_ret = subprocess.run(
        [sys.executable, str(Path(HERMES_HOME) / "scripts" / "vault-doctor.py"),
         "--vault", VAULT_MAIN, "--stale-days", "90"],
        capture_output=True, text=True, timeout=30
    )
    vd_output = vd_ret.stdout.strip()
    if vd_output:
        # Vault Doctor 有输出 = 有问题
        for line in vd_output.split("\n"):
            if "[WIKI]" in line or "[ORPH]" in line or "[STALE]" in line or "[DIR]" in line:
                issues.append(f"[VAULT] {line.strip()}")
except Exception:
    pass

# ── 8. Obsidian Junction 完整性 ──
try:
    # Windows Junction: os.path.islink() returns False for directory junctions,
    # but os.readlink() still works. Use readlink as the authoritative check.
    if not os.path.exists(VAULT_LINK) and not os.path.islink(VAULT_LINK):
        issues.append("❌ [VAULT] Hermes记忆 Junction 路径不存在")
    else:
        try:
            link_target = os.readlink(VAULT_LINK)
            # Normalize Windows path for comparison
            link_norm = os.path.normpath(link_target.replace("\\\\?\\", ""))
            main_norm = os.path.normpath(VAULT_MAIN)
            if link_norm != main_norm and not os.path.isdir(VAULT_MAIN):
                issues.append(f"❌ [VAULT] Junction 目标异常: {link_target} → {VAULT_MAIN} 不存在")
        except (OSError, ValueError):
            # readlink failed — might be a regular directory copy (stale)
            if os.path.isdir(VAULT_MAIN):
                issues.append("⚠️ [VAULT] Hermes记忆 是普通目录而非 Junction — 建议重建为 Junction")
            else:
                issues.append("❌ [VAULT] Hermes记忆 既非 Junction 也非有效目录")
except Exception:
    issues.append("❌ [VAULT] Junction 检查失败")

# ── 9. .obsidian 存在性 ──
obsidian_dir = os.path.join(VAULT_MAIN, ".obsidian")
if not os.path.isdir(obsidian_dir):
    issues.append("⚠️ [VAULT] .obsidian 目录缺失 — Obsidian 无法识别 vault")

# ── 10. SOUL.md 双写一致性 ──
try:
    import hashlib
    def md5_file(path):
        h = hashlib.md5()
        with open(path, "rb") as f:
            h.update(f.read())
        return h.hexdigest()
    if os.path.exists(SOUL_INTERNAL) and os.path.exists(SOUL_VAULT):
        if md5_file(SOUL_INTERNAL) != md5_file(SOUL_VAULT):
            issues.append("⚠️ [VAULT] SOUL.md 双写不一致 — 内部与 vault 版本不同")
    elif not os.path.exists(SOUL_VAULT):
        issues.append("⚠️ [VAULT] SOUL.md vault 副本不存在")
except Exception:
    pass

# ═══════════════════════════════════════════════════
# [MEMORY] 记忆层
# ═══════════════════════════════════════════════════

MEMORY_FILE = os.path.join(HERMES_HOME, "memories", "memory.md")
USER_FILE = os.path.join(HERMES_HOME, "memories", "user.md")

# ── 11. memory.md 容量 ──
# ── 11. memory.md 容量（按字符数，非字节）──
try:
    mem_content = open(MEMORY_FILE, "r", encoding="utf-8").read()
    mem_chars = len(mem_content)
    mem_limit = 20000
    mem_pct = mem_chars / mem_limit * 100
    if mem_pct > 80:
        issues.append(f"🔴 [MEMORY] memory.md 膨胀: {mem_chars}字符/{mem_limit} ({mem_pct:.0f}%)")
    elif mem_pct > 60:
        issues.append(f"⚠️ [MEMORY] memory.md 偏大: {mem_chars}字符/{mem_limit} ({mem_pct:.0f}%)")
    # instinct 数量检查
    instinct_count = mem_content.count("[instinct]")
    if instinct_count > 30:
        issues.append(f"⚠️ [MEMORY] instinct 过多: {instinct_count} 条 — 建议合并去重（目标 <20）")
except Exception:
    pass

# ── 12. user.md 容量 ──
# ── 12. user.md 容量（按字符数，非字节）──
try:
    user_content = open(USER_FILE, "r", encoding="utf-8").read()
    user_chars = len(user_content)
    user_limit = 10000
    user_pct = user_chars / user_limit * 100
    if user_pct > 80:
        issues.append(f"🔴 [MEMORY] user.md 超限: {user_chars}字符/{user_limit} ({user_pct:.0f}%)")
    elif user_pct > 60:
        issues.append(f"⚠️ [MEMORY] user.md 偏大: {user_chars}字符/{user_limit} ({user_pct:.0f}%)")
except Exception:
    pass

# ── 13. hot.md 新鲜度 ──
hot_path = os.path.join(VAULT_MAIN, "hot.md")
hot_age = file_age_hours(hot_path)
if hot_age < 0:
    issues.append("⚠️ [MEMORY] hot.md 不存在 — 跨会话热缓存缺失")
elif hot_age > 48:
    issues.append(f"⚠️ [MEMORY] hot.md 过期: {hot_age:.0f}h 未更新 (建议 <24h)")

# ═══════════════════════════════════════════════════
# [PIPE] 数据管道层
# ═══════════════════════════════════════════════════

# ── 14. Amber TMT 管道 ──
body, ok = curl_get("http://127.0.0.1:8010/api/v1/tmt/tree/default")
if ok:
    try:
        tree = json.loads(body)
        levels = tree.get("levels", {})
        l1 = levels.get("L1", {}).get("count", 0)
        l2 = levels.get("L2", {}).get("count", 0)
        l3 = levels.get("L3", {}).get("count", 0)
        l4 = levels.get("L4", {}).get("count", 0)
        l5 = levels.get("L5", {}).get("count", 0)
        total = l1 + l2 + l3 + l4 + l5
        if l1 > 0 and l2 == 0 and l3 == 0:
            issues.append(f"⚠️ [PIPE] TMT 蒸馏停滞: L1={l1} 但 L2/L3=0 — 蒸馏链可能断裂")
        elif l3 > 0 and l4 == 0:
            issues.append(f"⚠️ [PIPE] TMT 周级断层: L3={l3} 但 L4=0 — 周级蒸馏未运行")
        elif total == 0:
            pass  # No data at all, normal for fresh install
    except Exception:
        pass

# ── 15. 会话归档新鲜度 ──
archive_dir = os.path.join(VAULT_MAIN, "50_会话归档")
if os.path.isdir(archive_dir):
    # Recursively scan for .md files (archives may be in subdirs like 2026/)
    all_archives = []
    for root, dirs, files in os.walk(archive_dir):
        for f in files:
            if f.endswith(".md"):
                all_archives.append(os.path.join(root, f))
    if all_archives:
        latest = max(all_archives, key=os.path.getmtime)
        age = file_age_hours(latest)
        basename = os.path.basename(latest)
        if age > 72:
            issues.append(f"⚠️ [PIPE] 会话归档停滞: 最新归档 {age:.0f}h 前 ({basename})")
    else:
        issues.append("⚠️ [PIPE] 会话归档目录为空 — 归档 cron 可能未运行")
else:
    issues.append("⚠️ [PIPE] 50_会话归档 目录不存在")

# ── 16. 蒸馏日报落地 ──
current_month = datetime.now().strftime("%Y-%m")  # 用 YYYY-MM 匹配实际目录结构
distill_dir = os.path.join(VAULT_MAIN, "60_蒸馏日报", current_month)
if os.path.isdir(distill_dir):
    files = glob.glob(os.path.join(distill_dir, "*.md"))
    if not files and datetime.now().day > 3:
        issues.append(f"⚠️ [PIPE] {current_month} 蒸馏日报为空 — 回流 cron 可能未落地")
else:
    issues.append(f"⚠️ [PIPE] 60_蒸馏日报/{current_month}/ 目录不存在")

# ── 17. Honcho conclusions 数量 ──
body, ok = curl_post_json("http://127.0.0.1:8000/v3/workspaces/hermes/conclusions/list", {})
if ok:
    try:
        data = json.loads(body)
        total = data.get("total", 0)
        if total > 100:
            issues.append(f"⚠️ [PIPE] Honcho conclusions 过多: {total} 条 — 需要审查清理")
        # 检查结论是否停滞（最近结论超过 7 天）
        items = data.get("items", [])
        if items and total > 0:
            latest = max(i.get("created_at", "") for i in items)
            if latest:
                try:
                    latest_dt = datetime.fromisoformat(latest.replace("Z", "+00:00"))
                    days_stale = (datetime.now(latest_dt.tzinfo) - latest_dt).days
                    if days_stale > 7:
                        issues.append(f"⚠️ [PIPE] Honcho 结论停滞: 最新结论 {days_stale} 天前 — Deriver 可能未运行")
                except Exception:
                    pass
    except Exception:
        pass


# =============================================
# [P2-5/P3-7] 增强输出：周体检报告 + 自诊规则
# =============================================
try:
    # Pass issues as JSON env var to the enhancement script
    env = os.environ.copy()
    env['HEALTH_ISSUES'] = json.dumps(issues)
    subprocess.run(
        ['python', 'D:/知识库/工作台/30_项目建设/进行中/灵枢/_temp_health_append.py'],
        capture_output=False, timeout=30, env=env
    )
except Exception as e:
    print(f'enhancement script error: {e}')
