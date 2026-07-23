---
title: Kairos 接口规格书
aliases:
  - 接口规格
  - API Specification
tags:
  - kairos
  - design
  - api
created: 2026-07-20
updated: 2026-07-20
status: draft
---

# Kairos 接口规格书

> **定位**：定义 Kairos 系统的外部接口——REST API、Agent Tool、CLI 命令和事件总线消息格式。
>
> **基础 URL**：`http://localhost:8010`（可配置）
> **认证**：API Key（read/write/admin 三级），通过 `Authorization: Bearer <key>` 请求头传递。

---

## 一、REST API

### 1.1 记忆写入

**POST /v1/memories**

```json
{
  "path": "kairos://users/{id}/memories/",
  "content": "记忆内容",
  "contract": "ondemand",
  "memory_types": ["semantic"],
  "provenance": "user_input",
  "vad": {"v": 0.5, "a": 0.3, "d": 0.0},
  "relations": [
    {"target_id": "uuid", "relation_type": "causal", "strength": 0.8}
  ],
  "encoding_context": {"task": "review", "session_id": "uuid"}
}
```

**响应** `201 Created`：
```json
{"id": "uuid", "path": "kairos://users/{id}/memories/{uuid}", "version": 1}
```

**错误**：`400`（参数无效）、`401`（认证失败）、`403`（权限不足）、`413`（内容超长）、`422`（语义校验失败，如缺少必填字段）、`429`（请求过多，限流触发）

**POST /v1/memories/batch** — 批量导入（W-03）

**约束**：最大批量 100 条。非幂等——重复提交可能产生重复记录。部分失败返回 207 Multi-Status（成功条数 + 失败详情）。

```json
{
  "items": [
    {"path": "...", "content": "...", "contract": "ondemand", "provenance": "user_input", "memory_types": ["semantic"]},
    {"path": "...", "content": "...", "contract": "permanent", "provenance": "user_input", "memory_types": ["episodic"]}
  ],
  "on_conflict": "skip | overwrite"
}
```

**响应** `207 Multi-Status`：
```json
{
  "success_count": 8,
  "failed_count": 2,
  "results": [
    {"index": 0, "status": "created", "id": "uuid"},
    {"index": 1, "status": "error", "code": "ERR-INPUT-002", "message": "路径格式无效"}
  ]
}
```

### 1.2 记忆检索

**GET /v1/memories?path=kairos://users/{id}/memories/&limit=10&offset=0**

**GET /v1/memories?q=search+query&limit=5**

**GET /v1/memories/{id}**

**POST /v1/memories/search** — 五维混合检索（语义 + BM25 + 时序 + 信任 + 热度）

```json
{
  "query": "搜索内容",
  "mode": "hybrid",
  "weights": {"semantic": 0.4, "path": 0.3, "context": 0.15, "temporal": 0.1, "relational": 0.05},
  "limit": 10,
  "filters": {"contract": "permanent", "path_prefix": "kairos://projects/"}
}
```

**响应** `200`：标准检索结果列表（同 GET），加 `explanation` 字段说明各维度贡献。

**GET /v1/memories/heat-top?limit=10** — 热度最高记忆（heat_score 降序）

**响应** `200`：`{"data": [...], "total": N}`

**响应** `200 OK`：
```json
{
  "data": [
    {"id": "uuid", "path": "...", "content": "...", "contract": "...", "created_at": "..."}
  ],
  "total": 42,
  "path": "kairos://..."
}
```

### 1.3 记忆更新

**PATCH /v1/memories/{id}**（内部实现为版本插入，修改历史可审计，详见 data-model.md `superseded_by` 链）

**并发冲突**：请求头 `If-Match: {current_version}` 可选。提供时，服务端校验当前版本与请求一致后才执行更新；不一致返回 409 Conflict。不提供时直接更新（最后写入胜出）。

```json
{
  "content": "更新后的内容",
  "vad": {"v": 0.7, "a": 0.4, "d": 0.1}
}
```

**响应** `200 OK`：返回更新后的记忆对象（含新版本号）

**POST /v1/memories/{id}/feedback** — 可信度反馈

```json
{"feedback": "helpful|unhelpful|incorrect", "reason": "可选说明"}
```
**响应** `200`

**POST /v1/memories/{id}/lock** — 锁定保护（禁止修改/删除）

```json
{"reason": "合规保留", "duration_seconds": 2592000}
```
**响应** `200`

**POST /v1/memories/{id}/expire** — 标记过期（设 TTL，到期自动归档）

```json
{"ttl_seconds": 86400}
```
**响应** `200`

**POST /v1/memories/merge** — 语义合并（保留见证锚定，受 S-14 约束）

```json
{"source_ids": ["uuid1", "uuid2"], "strategy": "semantic_overlay"}
```
**响应** `200`：返回合并后新的记忆对象

### 1.4 记忆导出/删除/定向遗忘

**GET /v1/memories/{id}/export?clearance=export** — 导出记忆（脱敏）
- `?clearance=debug`（仅 localhost 可用）：返回完整内容，含原始 content、嵌入向量、审计字段
- `?clearance=export`（默认，所有网络可用）：返回脱敏摘要（content 前 200 字符 + 元数据，不包含嵌入向量和审计追踪）
```json
{
  "format": "json | markdown",
  "include_metadata": true
}
```
**响应** `200 OK`：导出格式的记忆完整内容

**DELETE /v1/memories/{id}** — 清除记忆
- permanent 契约：拒绝删除（返回 403）
- 常驻/按需/环境契约：软删除（标记 `is_deleted=true`，保留审计痕迹）
- 临时契约：硬删除（直接清除，不留审计痕迹，因 TTL 到期自动清除为其默认行为）

**POST /v1/memories/{id}/suppress** — 定向遗忘（抑制检索，保留数据）
```json
{"reason": "compliance_erase", "review_id": "uuid"}
```

### 1.5 路径操作

**GET /v1/path?path=kairos://users/{id}/** — 路径下记忆列表

**GET /v1/path/tree?path=kairos://users/** — 路径空间树状浏览

**POST /v1/path/suppress** — 路径级检索抑制（S-16/S-17）

```json
{"path_prefix": "kairos://_system/obsolete/", "reason": "compliance"}
```
**响应** `200`

### 1.6 校准与治理

**POST /v1/calibrate** — 发送外部校准信号（CAL-01）
```json
{
  "memory_id": "uuid",
  "narrative_coherence_score": 0.85,
  "source": "user_review"
}
```

**POST /v1/constitution** — 宪法级偏好管理（CAL-02，需 admin Key）
```json
{
  "action": "view | revise",
  "preference_key": "constitutional.preference.name",
  "new_value": "..."
}
```

**POST /v1/degradation/switch** — 降级模式切换（CAL-04，需 admin Key）
```json
{
  "mode": "conservative_silent | limited_cross_validation | safe_hibernation"
}
```

**POST /v1/freeze** — 强制冻结（CAL-03，需 admin Key）
```json
{"duration_seconds": 300, "scope": "all"}
```

**POST /v1/unfreeze** — 解冻

### 1.7 系统管理

**GET /health** — 健康检查（A-01）
```json
{"status": "ok", "components": {"api": "ok", "db": "ok", "scheduler": "running", "embedding": "ok", "sublimation": "idle"}, "uptime_seconds": 3600}
```

**GET /v1/config** — 查看配置（A-02）
**PATCH /v1/config** — 修改运行时配置（A-02）

**GET /v1/memories/stats** — 记忆库报告（总量/按类型/按状态/增长率）
```json
{"total": 1500, "by_type": {"semantic": 300, "episodic": 200, "procedural": 400, "narrative": 600}, "by_state": {"active": 1200, "stale": 200, "archived": 80, "superseded": 20}, "growth_7d": {"semantic": 15, "episodic": 8}}
```

**GET /v1/audit-log** — 审计日志查询（CAL-05）。以下参数为查询字符串参数：
```json
{
  "start_time": "ISO8601",
  "end_time": "ISO8601",
  "redline_id": "S-xx",
  "limit": 50
}
```

**GET /v1/falsification** — 证伪信号查询（CAL-06）。以下参数为查询字符串参数：
```json
{
  "detector": "coupling | vad_independence | system_aggregation",
  "since": "ISO8601"
}
```

**GET /v1/scheduler/status** — 调度器状态查询（A-03）

**POST /v1/webhooks** — 注册 Webhook 事件订阅（v1.1 预留端点）
```json
{
  "url": "https://agent.example.com/kairos-callback",
  "events": ["use_event", "calibration_signal", "degradation_switch"],
  "secret": "可选签名密钥"
}
```

**响应** `201 Created`：
```json
{"id": "webhook-uuid", "status": "active"}
```

> **升华状态查询**：升华/遗忘/重估状态通过 `GET /v1/sublimation/status` 查询（见下文）。

**POST /v1/seeds** — 种子锚点管理（需 admin Key）
```json
{
  "seed_type": "config | identity | calibration",
  "path": "kairos://_system/seeds/{name}",
  "content": {...},
  "initial_confidence": 0.9,
  "current_confidence": 0.9
}
```

**GET /v1/seeds** — 种子状态查看（A-05）
```json
{
  "seeds": [
    {"path": "kairos://_system/seeds/...", "status": "active", "degradation_level": 0.3}
  ]
}
```

**POST /v1/path/rebuild-index** — 路径索引重建（A-06）

**POST /v1/sublimation/trigger** — 手动触发升华（SF-02）
```json
{"path": "kairos://...", "target_stage": "strategy | behavior"}
```

**GET /v1/sublimation/status** — 升华进度查询（SF-04）
```json
{"queue": [{"id": "uuid", "stage": "raw", "status": "processing"}]}
```

---

## 二、Agent Tool

### Tool: memories_write

```json
{
  "name": "memories_write",
  "description": "向 Kairos 记忆系统写入一条记忆",
  "parameters": {
    "path": {"type": "string", "description": "存储路径"},
    "content": {"type": "string", "description": "记忆内容"},
    "contract": {"type": "string", "enum": ["permanent", "ondemand", "environmental", "temporary"]},
    "memory_types": {"type": "array", "items": {"type": "string", "enum": ["episodic", "narrative", "semantic", "procedural"]}, "description": "记忆类型列表，一条记忆可同时属于多类型（多重记忆认知模型）"},
    "vad": {"type": "object", "description": "情感坐标（可选）: {\"v\": float, \"a\": float, \"d\": float}"},
    "provenance": {"type": "string", "enum": ["user_input", "external_calibration", "internal_inference", "system_generated", "exploration"], "description": "来源标识（可选，默认 system_generated）"},
    "relations": {"type": "array", "items": {"type": "object"}, "description": "关系列表（可选）: [{\"target_id\": \"uuid\", \"relation_type\": \"causal\", \"strength\": 0.8}]"}
  }
}
```

### Tool: memories_search

```json
{
  "name": "memories_search",
  "description": "在 Kairos 记忆系统中搜索记忆",
  "parameters": {
    "query": {"type": "string"},
    "path": {"type": "string"},
    "limit": {"type": "integer", "default": 5}
  }
}
```

### Tool: path_browse

```json
{
  "name": "path_browse",
  "description": "浏览 Kairos 路径空间",
  "parameters": {
    "path": {"type": "string", "description": "起始路径，默认根"},
    "depth": {"type": "integer", "default": 2}
  }
}
```

### Tool: memories_list_recent

### Tool: memories_merge

```json
{
  "name": "memories_merge",
  "description": "语义合并多条记忆（保留见证锚定，受 S-14 约束）",
  "parameters": {
    "source_ids": {"type": "array", "items": {"type": "string", "format": "uuid"}, "description": "待合并的记忆 ID 列表"},
    "strategy": {"type": "string", "enum": ["semantic_overlay", "chronological_append"], "description": "合并策略"}
  }
}
```

```json
{
  "name": "memories_list_recent",
  "description": "列出最近使用的记忆（当前 session）",
  "parameters": {
    "limit": {"type": "integer", "default": 10}
  }
}
```

---

## 三、CLI 命令

| 命令 | 说明 | 示例 |
|:----|:-----|:-----|
| `kairos init` | 初始化系统（创建配置、目录和数据库） | `kairos init --db sqlite:///$HOME/.kairos/kairos.db` |
| `kairos serve` | 启动服务 | `kairos serve --port 8010` |
| `kairos write <path>` | 写入记忆 | `kairos write kairos://users/default/memories/ --content "..."` |
| `kairos read <path>` | 读取记忆 | `kairos read kairos://users/default/memories/abc` |
| `kairos search <query>` | 搜索 | `kairos search "关键词" --limit 10` |
| `kairos ls <path>` | 列出路径 | `kairos ls kairos://users/default/` |
| `kairos tree <path>` | 树状浏览 | `kairos tree kairos://projects/ --depth 3` |
| `kairos forget <id>` | 显式遗忘 | `kairos forget uuid` |
| `kairos suppress <id>` | 定向遗忘 | `kairos suppress uuid --reason compliance` |
| `kairos health` | 健康检查 | `kairos health` |
| `kairos config` | 配置管理 | `kairos config set KAIROS_DAILY_BUDGET_FEN 20000` |
| `kairos db` | 数据库管理 | `kairos db init` / `kairos db migrate` / `kairos db verify` / `kairos db backup` / `kairos db vacuum` / `kairos db reindex` |
| `kairos stop` | 停止服务 | `kairos stop` |
| `kairos logs` | 查看日志 | `kairos logs --tail 100` |
| `kairos audit verify-chain` | 审计链完整性验证 | `kairos audit verify-chain` |
| `kairos sublimation trigger` | 手动触发升华 | `kairos sublimation trigger --path kairos://projects/x/` |
| `kairos sublimation progress` | 查询升华进度 | `kairos sublimation progress` |
| `kairos calibrate` | 外部校准 | `kairos calibrate --memory-id uuid --score 0.85` |
| `kairos freeze` | 强制冻结 | `kairos freeze --duration 300` |
| `kairos status` | 系统状态 | `kairos status` 显示各层运行状态 |
| `kairos update <id>` | 更新记忆 | `kairos update uuid --content "new content"` |
| `kairos approve <id>` | 审批升华候选 | `kairos approve uuid --accept` |
| `kairos admin key generate` | 生成 API Key | `kairos admin key generate` |
| `kairos admin key rotate` | 轮换 API Key | `kairos admin key rotate <key_id>` |

---

## 四、事件总线消息格式

### 消息结构

```json
{
  "event_id": "uuid",
  "event_type": "calibration_signal | degradation_switch | use_event | intention_activate | intention_resolve | affective_boost | exploration_budget | latent_trigger | attention_allocation | sublimation_tick",
  "source": "storage_layer | strategy_layer | wm_layer | metacognition_layer | sovereignty_plane",
  "priority": 0,
  "payload": {},
  "timestamp": "2026-07-20T10:00:00Z",
  "ttl_seconds": 300
}
```

> **临时契约声明**：临时契约记忆在过期清除时不产生审计事件——其生命周期（创建→过期→清除）被视为瞬态操作，不留审计痕迹。此行为与 S-15（来源可鉴别）不冲突：临时契约在写入时仍记录 provenance，仅在过期清除阶段不产生审计日志。

**事件类型枚举**（完整定义以 `architecture-v1.0.0.md §10.10` 为准，此处仅列 v1.0 核心类型）：

| event_type | 说明 | 发送者 | 接收者 |
|-----------|:-----|:-------|:-------|
| `calibration_signal` | 外部校准信号注入 | 宪法主权面 | 全层广播 |
| `degradation_switch` | 降级模式切换 | 宪法主权面 | 全层广播 |
| `use_event` | 使用事件提交（影子副本、权重、审计） | WM | 策略+存储+元认知 |
| `intention_activate` | 前瞻保持触发条件匹配 | 策略 | WM |
| `intention_resolve` | 前瞻执行关闭裁定 | WM | 策略→存储 |
| `affective_boost` | 情感基线提升注入 | 策略 | WM |
| `exploration_budget` | 探索预算分配 | 元认知 | 策略 |
| `latent_trigger` | 潜伏势能重估触发 | 元认知 | 存储 |
| `attention_allocation` | 注意力分配日志 | 注意力调度器 | 元认知 |
| `sublimation_tick` | 升华管道轮次推进 | 存储 | 自身 |

---

## 五、记忆读取

### GET /v1/memories/{id}?level=summary|overview|full — 多级读取

**权限**：read

按粒度层级返回记忆内容：

| 层级 | 返回内容 | 适用场景 |
|:----|:---------|:---------|
| `summary` | 前 200 字摘要 + session 标签 | 快速预览 |
| `overview` | 前 800 字 + session 摘要 + 相关片段 | 常规检索 |
| `full` | 全文 + session 完整元数据 + 同 session 片段列表 | 深度分析 |

默认 `overview`。

---

### POST /v1/sublimation/prompt — 构建蒸馏提示词（两阶段 API 第一阶段）

**权限**：write

```json
{
  "session_id": "session-001",
  "records": [{"role": "user", "content": "..."}]
}
```

**响应**：`200` 返回 `prompt` 文本和 `record_ids` 列表。
调用方将 prompt 传给 LLM，将 LLM 返回结果提交到 `/v1/sublimation/process`。

---

### POST /v1/sublimation/process — 处理蒸馏结果（两阶段 API 第二阶段）

**权限**：write

```json
{
  "raw_response": "LLM 返回的 JSON 结果",
  "record_ids": ["rec-001"],
  "session_id": "session-001",
  "target_level": "L1"
}
```

**响应**：`200` 处理结果

---

### CLI 新增命令

| 命令 | 说明 | 示例 |
|:----|:-----|:-----|
| `kairos read --level summary` | 多级读取 | `kairos read uuid --level summary` |
| `kairos layers ls` | 列出 层级蒸馏各层概览 | `kairos layers ls --level L2` |
| `kairos layers distill` | 手动触发蒸馏 | `kairos layers distill --session-id xxx` |

---

## 六、扩展端点

### 6.1 会话消息 API

**POST /v1/sessions/{session_id}/messages** — 批量写入会话消息（Hermes on_session_end 调用）

**权限**：write

```json
{
  "messages": [
    {"role": "user", "content": "...", "tool_calls": null, "timestamp": 1234567890.0, "token_count": 150}
  ]
}
```

**响应** `200`：`{"status": "stored", "session_id": "...", "messages": 10}`

**GET /v1/sessions** — 列出最近会话

**权限**：read

**Query**：`?user_id=default&limit=20`

**GET /v1/sessions/{session_id}/messages** — 读取会话消息（支持游标分页）

**权限**：read

**Query**：`?limit=200&before_id=500`

### 6.2 实体知识图谱 API

**POST /v1/entities/extract** — 从文本提取实体

**权限**：write

```json
{
  "text": "文本内容",
  "user_id": "default"
}
```

**响应** `200`：`{"entities": [{"name": "...", "type": "concept", "description": "..."}], "count": 3}`

**POST /v1/graph/search** — 实体图谱多跳查询

**权限**：read

```json
{
  "query": "pgvector",
  "user_id": "default",
  "limit": 10,
  "relation_type": "causal"
}
```

**响应** `200`：`{"entities": [...], "relations": [...], "hops": 2}`

### 6.3 后台维护 API

**POST /v1/maintenance/run** — 手动触发后台维护（Light/Deep）

**权限**：admin

```json
{"mode": "light | deep", "user_id": "default"}
```

**GET /v1/maintenance/status** — 查看维护引擎运行状态

**权限**：read

**响应** `200`：`{"last_light_at": "...", "last_deep_at": "...", "total_merged": 42, "total_extracted_entities": 156}`

### 6.4 Reflect API（按需深度分析）

**POST /v1/reflect** — 对现有记忆执行按需深度分析

**权限**：read（分析）+ write（写入新洞察）

```json
{
  "query": "分析 Alice 的项目风险",
  "depth": "standard"
}
```

**执行流程**：
1. 对 query 执行 5D 混合检索，获取相关记忆
2. LLM 分析检索到的记忆，形成结构化洞察
3. 新洞察写入加工区（hall=processing），触发验证流程
4. 返回洞察结果

**响应** `200`：
```json
{
  "insight": "Alice 在 3 个项目中积累了前端架构经验...",
  "related_memories": ["mem_uuid1", "mem_uuid2"],
  "confidence": 0.78,
  "written_to": {"hall": "processing", "memory_id": "new_mem_uuid"}
}
```

**参数**：`depth` — `standard`（默认，快速分析）/ `deep`（更彻底分析，耗时更长）

### 6.5 健康报告与聚合统计

**GET /v1/health/detail** — 聚合健康报告

**权限**：read

**响应** `200`：
```json
{
  "total_memories": 1500,
  "by_type": {"semantic": 300, "episodic": 200, "procedural": 400, "narrative": 600},
  "by_state": {"active": 1200, "stale": 200, "archived": 80, "suppressed": 30, "superseded": 20},
  "growth_7d": {"semantic": 15, "episodic": 8},
  "flags": {"needs_verification": 5, "contradiction": 2, "p6_deviation": true},
  "rl_weights": {"relevance": 0.42, "recency": 0.18, "frequency": 0.15, "user_feedback": 0.14, "trust_score": 0.11},
  "maintenance": {"last_light": "ISO8601", "last_deep": "ISO8601"}
}
```

**GET /v1/evolution/{knowledge_id}** — 查询知识演化链

**权限**：read

**响应** `200`：`{"knowledge_id": "...", "chain": [{"source_id": "...", "target_id": "...", "relation_type": "replaces", "confidence": 0.85}]}`

### 6.6 Playbook API

**POST /v1/playbooks** — 创建 Playbook candidate

**权限**：write

```json
{
  "task_class": "deployment",
  "title": "Docker deploy with rollback",
  "trigger": "用户请求部署",
  "goal": "实现零停机部署",
  "steps": [{"number": 1, "capability_class": "shell", "action": "docker build ...", "evidence_required": true, "why": "确保一致性"}],
  "pitfalls": [{"description": "端口冲突", "frequency": 0.3}],
  "verification": ["curl health-check"],
  "cleanup": ["docker rm temp"],
  "related_skills": ["devops"]
}
```

**响应** `201`：`{"id": "pb_abc123", "status": "candidate", "confidence": 0.5}`

**GET /v1/playbooks/search** — 搜索 Playbook

**权限**：read

**Query**：`?query=docker+deploy&task_class=deployment&status=promoted&limit=5`

**POST /v1/playbooks/{id}/feedback** — 记录 Playbook 使用反馈

**权限**：write

```json
{
  "outcome": "success | partial | failed | stale | misleading",
  "evidence": ["health-check passed"],
  "preconditions_checked": ["port 80 free"],
  "steps_completed": [1, 2, 3],
  "model_name": "gpt-4"
}
```

**响应** `200`：`{"id": "pb_abc123", "outcome": "success", "status": "promoted", "confidence": 0.65}`

### 6.7 Recall Funnel API

**GET /v1/search/explain** — 检索附带 recall funnel trace

**权限**：read

**Query**：`?q=docker&include_trace=true`

**响应** `200`：
```json
{
  "results": [...],
  "trace": {
    "stages": {"lexical_candidates": 200, "vector_candidates": 150, "final_candidates": 10, "returned": 5},
    "timings_ms": {"total": 245, "lexical": 30, "vector": 180, "rerank": 35},
    "character_budget": 3000
  }
}
```

### 6.8 MCP Bridge 工具映射

**GET /v1/search/explain**

MCP Bridge 不通过 REST API 暴露，而是通过独立的 MCP 服务器进程注册到 Hermes Agent。技术规格见 `src/access/mcp/bridge.py`。工具清单见架构文档 §7.3。

| 工具 | 功能 | 等价 REST 操作（内部路由映射，部分非独立公开端点） |
|:----|:-----|:--------------|
| `kairos_store_memory` | 存储记忆 | POST /v1/memories |
| `kairos_search_memories` | 五维混合检索 | POST /v1/memories/search （定义见 §一） |
| `kairos_get_hot_memories` | 热度最高记忆 | GET /v1/memories/heat-top （定义见 §一） |
| `kairos_search_graph` | 图谱检索 | POST /v1/graph/search |
| `kairos_extract_entities` | 实体提取 | POST /v1/entities/extract |
| `kairos_feedback_memory` | 可信度反馈 | POST /v1/memories/{id}/feedback （定义见 §一） |
| `kairos_calibrate` | 校准信号 | POST /v1/calibrate |
| `kairos_get_stats` | 记忆库报告 | GET /v1/memories/stats （定义见 §一） |
| `kairos_search_sessions` | 会话搜索 | GET /v1/sessions |
| `kairos_tree` | 路径浏览 | GET /v1/path/tree |

### 6.9 知识加工区 API

**POST /v1/halls/promote** — 将记忆从加工区推进到验证区或正式库

**权限**：write

```json
{
  "memory_id": "uuid",
  "target_hall": "validation | canonical",
  "gate_notes": "差异检验通过，P6 合规"
}
```

**响应** `200`：`{"memory_id": "uuid", "from": "processing", "to": "validation", "gate": "passed"}`

**POST /v1/halls/demote** — 将记忆从验证区退回加工区

**权限**：write

```json
{
  "memory_id": "uuid",
  "reason": "差异检验未通过，待重新蒸馏"
}
```

**响应** `200`：`{"memory_id": "uuid", "from": "validation", "to": "processing"}`

**GET /v1/halls/{hall}** — 查询指定区域内的记忆列表

**权限**：read

**Query**：`?user_id=default&limit=20`

### 6.10 端云同步 API

**POST /v1/sync/push** — 推送本地增量修改至服务端

**权限**：write

```json
{
  "user_id": "default",
  "batch": [
    {"memory_id": "uuid", "operation": "update", "sync_version": 5, "content": "..."}
  ]
}
```

**响应** `200`：`{"synced": 10, "conflicts": 1, "conflict_ids": ["uuid"]}`

**冲突解决策略**：以服务端见证锚定为主副本仲裁。终端推送时若 sync_version 冲突（终端版本 < 服务端当前版本），服务端返回 conflict 标记，终端在下一同步周期接收服务端裁决结果（以服务端内容为准）。

**POST /v1/sync/pull** — 拉取服务端增量变更

**权限**：read

```json
{
  "user_id": "default",
  "last_synced_at": "ISO8601",
  "limit": 100
}
```

**响应** `200`：`{"memories": [...], "pulled_version": 42, "has_more": false}`

**POST /v1/sync/export** — 导出完整数据快照（.kairos 格式）

**权限**：read

```json
{"user_id": "default", "include_vectors": true}
```

**响应** `200`：返回 `.kairos` 二进制文件

**POST /v1/sync/import** — 导入数据快照

**权限**：admin

```json
{"file": ".kairos 二进制数据", "mode": "merge"}
```

---

## 七、错误码体系

> **说明**：以下为 HTTP 级错误码子集。完整内部错误码集（含 DB/LLM/SYS 类）见 `references/error-reference.md`。调用方应仅按此表处理 API 响应中的错误码。

| 错误码 | HTTP 状态 | 说明 | 恢复建议 |
|:------|:---------|:-----|:---------|
| `ERR-AUTH-001` | 401 | API Key 无效 | 检查 `KAIROS_API_KEY` |
| `ERR-AUTH-002` | 401 | API Key 已过期/被吊销 | 生成新 Key |
| `ERR-AUTH-003` | 403 | 权限不足 | 升级 API Key 级别 |
| `ERR-RATE-001` | 429 | 写入限流 | 等待后重试 |
| `ERR-RATE-002` | 429 | 读取限流 | 等待后重试 |
| `ERR-INPUT-001` | 413 | 内容超长 | 减少内容长度 |
| `ERR-INPUT-002` | 400 | 路径格式无效 | 检查 kairos:// 格式 |
| `ERR-INPUT-004` | 422 | 语义校验失败（缺少必填字段，如 content / path） | 检查请求体必填字段 |
| `ERR-SEC-001` | 403 | 安全红线违反 | 检查操作是否符合红线约束 |

> **说明**：`ERR-DB-*`、`ERR-LLM-*`、`ERR-SYS-*` 为内部运维与日志使用码，API 不直接返回。上表仅列出 HTTP 级错误码。完整错误码集见 `references/error-reference.md`。

---

## 版本记录

| 版本 | 日期 | 变更 |
|:----|:----|:-----|
| v1.0.0 | 2026-07-23 | 初始接口规格。REST API 57 个端点（含批量导入/导出/宪法管理/降级切换/审计/证伪/调度器/种子/升华触发/升华进度）+ 5 个 Agent Tool（含 memories_merge）+ 27 个 CLI 命令 + 10 个 MCP 工具 + 消息格式 + 错误码。 |
