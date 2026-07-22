---
name: amber-bridge
description: "Amber OS 桥接：Hermes 对话归档至 Amber、TMT 蒸馏触发、蒸馏结果回流、5维搜索。连接 Hermes 记忆系统与 Amber 记忆炼制层。"
version: 1.2.0
platforms: [windows]
metadata:
  hermes:
    tags: [amber, memory, tmt, distillation, bridge]
    category: hermes
    related_skills: [vault-sync, honcho-operations, memory-provider-management]
---

# Amber Bridge

Hermes 与 Amber OS 的桥接层。Amber 管"记忆的炼制"，Hermes 管"记忆的使用"。

## 架构

```\nHermes Agent ──▶ Amber API (:8010) ──▶ PostgreSQL + pgvector (:5433)\n    │                    │\n    │                    ├── TMT 蒸馏（L1→L2→L3→L4 预处理）\n    │                    ├── 5维检索 + Chunk 检索\n    │                    ├── FTS5 降级语义搜索（嵌入不可达时自动 fallback）\n    │                    └── 冗余合并（余弦相似度 / 关键词降级）\n    │\n    ├── Builtin memory() ──▶ SQLite\n    ├── Honcho ──▶ 辨证推理\n    └── Obsidian Vault ──▶ 用户可编辑\n```

## API 端点

基础 URL: `http://127.0.0.1:8010`

### 记忆操作
- `POST /api/v1/memories` — 写入记忆
- `POST /api/v1/memories/search` — 5维搜索
- `POST /api/v1/memories/search-chunks` — Chunk 级搜索
- `GET /api/v1/memories/stats` — 统计信息

### TMT 蒸馏
- `POST /api/v1/tmt/consolidate/session` — L1→L2
- `POST /api/v1/tmt/consolidate/daily` — L2→L3
- `POST /api/v1/tmt/consolidate/weekly` — L3→L4
- `POST /api/v1/tmt/consolidate/monthly` — L4→L5
- `GET /api/v1/tmt/tree/{user_id}` — 查看记忆树

### 会话归档
- `POST /api/v1/sessions/archive` — 完整对话入宫（内容转文本推送）

### 反思
- `POST /api/v1/reflect?user_id={uid}&mode={mode}` — 触发反思（参数为查询参数，非 body；`user_id` 必填）

### 图谱
- `POST /api/v1/graph/search` — 知识图谱搜索

### 健康
- `GET /api/v1/health/{user_id}` — 用户记忆健康度

## 使用示例

### 写入记忆
```bash
DATA='{"content":"记忆内容","user_id":"default","category":"fact"}'
curl -s -X POST "http://127.0.0.1:8010/api/v1/memories" \
  -H "Content-Type: application/json" -d "$DATA"
```

### 搜索记忆
```bash
DATA='{"query":"搜索词","user_id":"default","top_k":5}'
curl -s -X POST "http://127.0.0.1:8010/api/v1/memories/search" \
  -H "Content-Type: application/json" -d "$DATA"
```

### 触发 TMT 蒸馏
```bash
# L1→L2（碎片→会话）
curl -s -X POST "http://127.0.0.1:8010/api/v1/tmt/consolidate/session" \
  -H "Content-Type: application/json" -d '{"user_id":"default"}'

# L2→L3（会话→日报）
DATE=$(date '+%Y-%m-%d')
curl -s -X POST "http://127.0.0.1:8010/api/v1/tmt/consolidate/daily" \
  -H "Content-Type: application/json" -d "{\"user_id\":\"default\",\"date\":\"$DATE\"}"
```

### 查看记忆树
```bash
curl -s "http://127.0.0.1:8010/api/v1/tmt/tree/default"
```

## 会话归档流程

Hermes cron job 每日 08:00/20:00 执行：

1. `session_search()` 获取最近会话
2. 提取用户+助手消息，拼接为纯文本（跳过工具输出）
3. `POST /api/v1/sessions/archive` 推送到 Amber
4. Amber 自动：L1 碎片入库 → 实体提取 → 图谱更新

**Payload 格式（已验证）：**
```bash
# 提取对话文本
SESSION_ID="20260628_092232_0fee38a9"
PAYLOAD='{"user_id":"default","session_id":"SESSION_ID","content":"[user] 问题\n[assistant] 回答\n..."}'
curl -s -X POST "http://127.0.0.1:8010/api/v1/sessions/archive" \
  -H "Content-Type: application/json" -d "$PAYLOAD"
# 成功响应：{"archived":true,"memory_id":N}
```

**关键：** `content` 字段必须是纯文本字符串，传入结构化消息数组会被拒绝。

## TMT 蒸馏链

Amber 管道 cron 每天 09:00/14:00 执行统一脚本 `amber-pipeline.py`，按顺序完成：

```
Step 1: 轻量反思（热度衰减）→ POST /api/v1/reflect?user_id=default&mode=light
Step 2: TMT 蒸馏 L1→L2→L3 → POST /api/v1/tmt/consolidate/session + /daily
Step 3: 深度反思（实体提取）→ POST /api/v1/reflect?user_id=default&mode=deep
Step 4: 蒸馏结果回流 → 写入 D:/知识库/Hermes记忆/60_蒸馏日报/YYYY-MM/DD-DD.md
```

每步先检查前置条件，无数据时 `[SKIP]`，有数据时 `[RUN]`。

## 蒸馏结果回流

由 `amber-pipeline.py` Step 4 自动完成：

1. 调用 `POST /api/v1/tmt/consolidate/daily` 获取日报数据（注意：`tmt/tree` 只返回聚合计数，不返回节点详情）
2. 用返回的 summary + heat_score 写入 `D:/知识库/Hermes记忆/60_蒸馏日报/YYYY-MM/YYYY-MM-DD.md`

## 端口分配

| 服务 | 端口 | 说明 |\n|------|------|------|\n| Honcho DB | :5432 | PostgreSQL + pgvector |\n| Honcho API | :8000 | 辨证推理 |\n| Amber DB | :5433 | PostgreSQL + pgvector |\n| Amber API | :8010 | 记忆炼制 |\n\n注：2026-07-06 移除 AGE 扩展，TMT 表已从 ag_catalog schema 迁移至 public。llama-server 已关闭自启，嵌入降级为 FTS5。

## Cron 任务全景（8个）

所有任务在 **09:00-23:00** 窗口内运行（用户不保证 23:00-09:00 Hermes 在线）。

### 主任务

| 时间 | 任务 | 类型 |
|------|------|------|
| 09:00/14:00 | Amber 管道（反射→蒸馏→反思→回流） | 脚本 |
| 10:30/21:00 | 记忆基础设施监控 | 脚本 |
| 08:00/20:00 | 会话归档与学习 | Agent |
| 18:00 | 每日维护 | Agent |
| 21:00 | 日报生成 | Agent |
| 22:30 | 工作台巡检 | Agent |
| Fri 17:30 | 周报生成 | Agent |
| 月末 19:00 | 月报生成 | Agent |

所有补跑脚本遵循统一模式：
1. 前置检查（API 可达性）
2. 数据检查（是否有未处理数据）
3. 已完成检查（是否已被主任务处理）
4. 条件执行（仅在需要时补跑）
5. 输出状态：`[SKIP]` / `[RUN]` / `[DONE]` / `[FAIL]`

TMT 蒸馏天然幂等——API 处理"未蒸馏的 L1 碎片"，已蒸馏的不重复处理。即使主任务和补跑都执行了，也不会产生重复数据。

## 脚本清单

| 脚本 | 用途 |
|------|------|
| `scripts/amber-pipeline.py` | 统一管道：反射→蒸馏→反思→回流（09:00/14:00）+ L3→L4 周级蒸馏（周日自动触发） |
| `scripts/memory-system-startup.py` | 电脑重启后自动编排：Docker→容器→deriver patch→健康检查（llama-server 自启已于 2026-07-06 移除） |
| `scripts/memory-system-startup.vbs` | 静默启动包装器（等15s后调用pythonw） |
| `scripts/memory-infra-health.py` | 记忆系统健康监控（10:30/21:00）— 4层19项检查：基础设施/知识库/记忆质量/数据管道。含 honcho-deriver 存活检查、memory/user 容量按字符数检查、instinct 数量检查、TMT L4/L5 断层检查、Honcho 结论停滞检查。空输出=健康=静默。 |

## Pitfalls

1. **Git Bash curl 转义问题** — `-d '{"key":"value"}'` 在 Git Bash 中可能被转义破坏。用变量：`DATA='{"key":"value"}'; curl -d "$DATA"`
2. **Embedding 格式** — Amber 的 embedding.py 已修复为 OpenAI 兼容格式（`input: [text]`），与 llama-server 兼容
3. **main.py 绑定地址** — 已修复为使用 config 中的 `HOST`（0.0.0.0），而非硬编码 127.0.0.1
4. **uvicorn 依赖** — `requirements-hermes.txt` 已添加 uvicorn，用 `Dockerfile.hermes` 构建
5. **容器重建后需重新构建镜像** — 修改 src/ 代码后必须 `docker build -t amber-api -f Dockerfile.hermes .` 再重建容器
6. **AGE 已移除（2026-07-06）** — AGE 扩展和 ag_catalog schema 已卸载，TMT 核心表从 ag_catalog 迁移至 public。`search_path` 只需 `"$user", public`。如果遇到 `relation "tmt_xxx" does not exist`，请检查当前连接是否能看到 public 中的表：`\dt public.*`。残留的 `ag_catalog` schema（空）可忽略，不影响运行。\n7. **Embedding 模型名不受影响** — 由于 FTS5 降级，嵌入服务不再作为强依赖。如果后续需要恢复远程嵌入，模型名由 `EMBEDDING_MODEL` 环境变量指定，无约束。\n
9. **所有 curl 用 `127.0.0.1` 而非 `localhost`** — 其他进程（如 `python -m http.server 8080`）可以绑定 `0.0.0.0:x`，拦截 `localhost:x` 请求。已发生：2026-06-27，stale `python -m http.server 8080` 进程导致关联健康检查误报 llama-server 不可达。本技能所有 API 示例已统一使用 `127.0.0.1`。

11. **`/api/v1/sessions/archive` 接受纯文本而非结构化消息** — `content` 字段必须是纯文本字符串。传入 `{"messages": [{"role":"user","content":"..."}]}` 会报 `Field required` / `Input should be a valid string` 错误。正确格式：`{"user_id":"default","session_id":"...","content":"对话文本"，可选"summary":"..."}`。已验证于 2026-06-28。

12. **`stats.by_tier` 与 `tmt/tree` 计数不一致** — `GET /memories/stats?user_id=default` 的 `by_tier` 字段和 `GET /tmt/tree/{user_id}` 的 `levels` 字段可能报告不同的 L1/L2 计数。已验证：stats 说全部是 L2，tree 说全部是 L1。**以 `tmt/tree` 为准**——TMT 蒸馏 API（consolidate/session）实际处理的是 tree 定义的 L1。管道脚本中检测"是否有未蒸馏碎片"必须用 `tmt/tree` 而非 `stats.by_tier`。

13. **`tmt/tree` 不返回节点详情** — `GET /tmt/tree/{user_id}` 只返回每个层级的 `count` 和 `avg_heat`，不返回节点列表或详情。蒸馏回流（写日报文件）不能从 tree 端点获取内容，必须直接用 `consolidate/daily` 的返回值（包含 `summary`、`heat_score`、`id`）。

14. **死脚本累积** — 每次将 .sh 脚本迁移到 .py 后，旧 .sh 文件不会自动删除。定期检查 `~/AppData/Local/hermes/scripts/` 中无 cron 引用的文件并清理。判断方法：cron 列表中没有引用该脚本名 = 死脚本。

15. **Embedding FTS5 降级模式（2026-07-06）** — llama-server 已关闭自启，`core/embedding.py` 中 `get_embedding()` 在嵌入服务不可达时返回空列表并记录 WARN 日志，不阻塞主流程。如果后续需要恢复嵌入，需：`EMBEDDING_ENDPOINT` 指向可用的 OpenAI 兼容 API，或手动启动 llama-server。

16. **TMT L4 周级蒸馏（2026-07-06 重构）** — L4 不独立输出，作为 Layer 3 自主反思的预处理层（周日 17:00 跑，18:00 Layer 3 读数据）。L5（月级）已废弃——月报已覆盖月度摘要。TMT 蒸馏不再依赖 embedding 服务，嵌入不可达时降级为关键词聚类。

17. **`/api/v1/reflect` 参数是查询参数不是 body** — 端点签名 `reflect(user_id: str, mode: str = "light")`，`user_id` 是必填查询参数。传 JSON body `{"mode":"light"}` 会 422 Unprocessable Entity。正确调用：`curl -X POST "http://127.0.0.1:8010/api/v1/reflect?user_id=default&mode=light"`。已修复于 2026-07-04。
