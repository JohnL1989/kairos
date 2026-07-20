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
status: v1.0.0
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
  "memory_type": "semantic",
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

**错误**：`400`（参数无效）、`401`（认证失败）、`403`（权限不足）、`413`（内容超长）

**POST /v1/memories/batch** — 批量导入（W-03）

```json
{
  "items": [
    {"path": "...", "content": "...", "contract": "ondemand", "memory_type": "semantic"},
    {"path": "...", "content": "...", "contract": "permanent", "memory_type": "episodic"}
  ],
  "on_conflict": "skip | overwrite"
}
```

### 1.2 记忆检索

**GET /v1/memories?path=kairos://users/{id}/memories/&limit=10&offset=0**

**GET /v1/memories?q=search+query&limit=5**

**GET /v1/memories/{id}**

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

**PATCH /v1/memories/{id}**

```json
{
  "content": "更新后的内容",
  "vad": {"v": 0.7, "a": 0.4, "d": 0.1}
}
```

**响应** `200 OK`：返回更新后的记忆对象

### 1.4 记忆导出/删除/定向遗忘

**GET /v1/memories/{id}/export** — 记忆导出（M-06）
```json
{
  "format": "json | markdown",
  "include_metadata": true
}
```
**响应** `200 OK`：导出格式的记忆完整内容

**DELETE /v1/memories/{id}** — 硬删除（仅临时契约允许）

**POST /v1/memories/{id}/suppress** — 定向遗忘（抑制检索，保留数据）
```json
{"reason": "compliance_erase", "review_id": "uuid"}
```

### 1.5 路径操作

**GET /v1/path?path=kairos://users/{id}/** — 路径下记忆列表

**GET /v1/path/tree?path=kairos://users/** — 路径空间树状浏览

### 1.6 校准与治理

**POST /v1/calibrate** — 发送外部校准信号（C-01）
```json
{
  "memory_id": "uuid",
  "narrative_coherence_score": 0.85,
  "source": "user_review"
}
```

**POST /v1/constitution** — 宪法级偏好管理（C-02，需 admin Key）
```json
{
  "action": "view | revise",
  "preference_key": "constitutional.preference.name",
  "new_value": "..."
}
```

**POST /v1/degradation/switch** — 降级模式切换（C-04，需 admin Key）
```json
{
  "mode": "conservative_silent | limited_cross_validation | safe_hibernation"
}
```

**POST /v1/freeze** — 强制冻结（C-03，需 admin Key）
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

**GET /v1/audit-log** — 审计日志查询（C-05）
```json
{
  "start_time": "ISO8601",
  "end_time": "ISO8601",
  "redline_id": "S-xx",
  "limit": 50
}
```

**GET /v1/falsification** — 证伪信号查询（C-06）
```json
{
  "detector": "coupling | vad_independence | system_aggregation",
  "since": "ISO8601"
}
```

**GET /v1/scheduler/status** — 调度器状态查询（A-03）
```json
{
  "sublimation": {"status": "idle | running", "queue_length": 0},
  "forgetting": {"status": "idle | scanning", "candidates": 0},
  "revaluation": {"status": "idle | active", "scan_progress": "0%"}
}
```

**POST /v1/seeds** — 冷启动种子注入（A-04，需 admin Key）
```json
{
  "seed_type": "config | identity | calibration",
  "path": "kairos://_system/seeds/{name}",
  "content": {...}
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
    "memory_type": {"type": "string", "enum": ["episodic", "narrative", "semantic", "procedural"]}
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
| `kairos write <path>` | 写入记忆 | `kairos write kairos://users/default/memories/ --content "..."` |
| `kairos read <path>` | 读取记忆 | `kairos read kairos://users/default/memories/abc` |
| `kairos search <query>` | 搜索 | `kairos search "关键词" --limit 10` |
| `kairos ls <path>` | 列出路径 | `kairos ls kairos://users/default/` |
| `kairos tree <path>` | 树状浏览 | `kairos tree kairos://projects/ --depth 3` |
| `kairos forget <id>` | 显式遗忘 | `kairos forget uuid` |
| `kairos suppress <id>` | 定向遗忘 | `kairos suppress uuid --reason compliance` |
| `kairos health` | 健康检查 | `kairos health` |
| `kairos config` | 配置管理 | `kairos config set KAIROS_DAILY_BUDGET 200` |
| `kairos calibrate` | 外部校准 | `kairos calibrate --memory-id uuid --score 0.85` |
| `kairos freeze` | 强制冻结 | `kairos freeze --duration 300` |
| `kairos status` | 系统状态 | `kairos status` 显示各层运行状态 |

---

## 四、事件总线消息格式

### 消息结构

```json
{
  "event_id": "uuid",
  "event_type": "memory_write | memory_retrieve | sublimation_stage | forgetting_trigger | calibration_arrival | freeze_activate | degradation_switch",
  "source": "storage_layer | pm_layer | wm_layer | metacognition_layer | sovereignty_plane",
  "priority": 0,
  "payload": {},
  "timestamp": "2026-07-20T10:00:00Z",
  "ttl_seconds": 300
}
```

### 事件类型枚举

| event_type | 说明 | 发送者 | 接收者 |
|-----------|:-----|:-------|:-------|
| `memory_write` | 记忆写入完成 | 存储层 | WM 层、元认知层 |
| `memory_retrieve` | 记忆检索完成 | 存储层 | WM 层、策略层 |
| `sublimation_stage` | 升华阶段变更 | 存储层 | 元认知层 |
| `forgetting_trigger` | 遗忘触发 | 存储层 | 元认知层 |
| `calibration_arrival` | 外部校准到达 | 宪法主权面 | 全层广播 |
| `freeze_activate` | 冻结激活 | 宪法主权面 | 全层广播 |
| `degradation_switch` | 降级模式切换 | 宪法主权面 | 全层广播 |
| `bias_alert` | 偏置告警 | 元认知层 | 宪法主权面 |
| `probe_response` | 探针响应 | 存储层 | 元认知层 |
| `seed_lifecycle` | 种子生命周期事件 | 元认知层 | 宪法主权面 |
| `attention_allocation` | 注意力分配日志 | WM 层 | 元认知层 |

---

## 五、错误码体系

| 错误码 | HTTP 状态 | 说明 | 恢复建议 |
|:------|:---------|:-----|:---------|
| `ERR-AUTH-001` | 401 | API Key 无效 | 检查 `KAIROS_API_KEY` |
| `ERR-AUTH-002` | 403 | 权限不足 | 升级 API Key 级别 |
| `ERR-RATE-001` | 429 | 写入限流 | 等待后重试 |
| `ERR-RATE-002` | 429 | 读取限流 | 等待后重试 |
| `ERR-INPUT-001` | 413 | 内容超长 | 减少内容长度 |
| `ERR-INPUT-002` | 400 | 路径格式无效 | 检查 kairos:// 格式 |
| `ERR-DB-001` | 503 | 数据库连接失败 | 检查数据库状态 |
| `ERR-DB-002` | 500 | 数据库迁移失败 | 回滚迁移 |
| `ERR-LLM-001` | 503 | LLM 调用超时 | 检查 LLM 端点 |
| `ERR-LLM-002` | 429 | LLM 日预算耗尽 | 等待预算重置 |
| `ERR-SEC-001` | 403 | 安全红线违反 | 检查操作是否符合红线约束 |

---

## 版本记录

| 版本 | 日期 | 变更 |
|:----|:----|:-----|
| v1.0.0 | 2026-07-20 | 初始接口规格。REST API 20+ 端点（含批量导入/导出/宪法管理/降级切换/审计/证伪/调度器/种子/升华触发/升华进度）+ 4 个 Agent Tool + 12 个 CLI 命令 + 消息格式 + 错误码。 |
