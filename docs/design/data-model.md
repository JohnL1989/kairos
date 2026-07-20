---
title: Kairos 数据模型设计
aliases:
  - 数据模型
  - Data Model
tags:
  - kairos
  - design
  - data-model
created: 2026-07-20
updated: 2026-07-20
status: v1.0.0
---

# Kairos 数据模型设计

> **定位**：定义 Kairos 系统的核心数据存储结构。架构文档 §4 定义了存储层的行为约束，本文定义具体的 Schema 设计。
>
> **存储后端**：标准模式 PostgreSQL + pgvector，轻量模式 SQLite + sqlite-vec。

---

## 一、核心记忆表

### memories（主记忆表）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | 全局唯一记忆 ID |
| `path` | TEXT | NOT NULL, UNIQUE(path, version) | kairos:// 路径 |
| `version` | INTEGER | DEFAULT 1 | 版本号，更新时递增 |
| `content` | TEXT | NOT NULL | 记忆内容 |
| `content_hash` | TEXT | NOT NULL | SHA-256(content) |
| `embedding` | VECTOR(n) | — | 语义向量（n 取决于嵌入模型维度） |
| `memory_type` | TEXT | NOT NULL | 枚举：episodic / narrative / semantic / procedural |
| `contract` | TEXT | NOT NULL, DEFAULT 'ondemand' | 契约类型：permanent / ondemand / environmental / temporary |
| `provenance` | TEXT | NOT NULL | 来源：external_calibration / internal_inference / user_input / system_generated / exploration |
| `status` | TEXT | NOT NULL, DEFAULT 'active' | active / archived / suppressed / superseded |
| `is_identity` | BOOLEAN | DEFAULT FALSE | 是否为身份记忆 |
| `is_structure` | BOOLEAN | DEFAULT FALSE | 是否为结构性记忆（认知完整性轴） |
| `calibration_confidence` | FLOAT | DEFAULT 0.5, [0,1] | 校准置信度 |
| `vad_v` | FLOAT | DEFAULT 0, [-1,1] | 情感效价（Valence） |
| `vad_a` | FLOAT | DEFAULT 0, [-1,1] | 情感唤醒度（Arousal） |
| `vad_d` | FLOAT | DEFAULT 0, [-1,1] | 情感支配度（Dominance） |
| `decontextualization_level` | FLOAT | DEFAULT 0, [0,1] | 去语境化程度，升华时递增 |
| `encoding_context` | JSONB | — | 编码情境（时空上下文/任务目标/关联记忆ID） |
| `created_at` | TIMESTAMPTZ | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMPTZ | NOT NULL | 最后更新时间 |
| `superseded_by` | UUID | REFERENCES memories(id) | 被取代的新记忆 ID（修正场景） |

**索引**：
- `idx_memories_path` ON `path`（支持前缀查询）
- `idx_memories_contract` ON `contract`
- `idx_memories_type` ON `memory_type`
- `idx_memories_created` ON `created_at`
- `idx_memories_identity` ON `is_identity` WHERE `is_identity = TRUE`
- `idx_memories_status` ON `status`
- `idx_memories_embedding` 向量索引（pgvector: IVFFlat 或 HNSW）

### memory_relations（关系索引表）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `source_id` | UUID | FK → memories(id) | 源记忆 |
| `target_id` | UUID | FK → memories(id) | 目标记忆 |
| `relation_type` | TEXT | NOT NULL | causal / independent / hierarchical / competitive / part_whole。前四类对应认知基础四类关系（因果/部分独立/弱层级/竞争），`part_whole` 为粒度组合关系（父子记忆组成关系，对应认知基础「记忆粒度性质」声明）——与四类对等关系不同属一个分类轴。
| `strength` | FLOAT | DEFAULT 1.0, [0,1] | 关系强度 |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

### memory_tags（记忆标签表）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `memory_id` | UUID | FK → memories(id), ON DELETE CASCADE | |
| `key` | TEXT | NOT NULL | 标签键 |
| `value` | TEXT | — | 标签值 |

---

## 二、双副本存储

### witness_anchor（见证锚定主副本）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `memory_id` | UUID | PK, FK → memories(id) | 对应记忆 |
| `narrative_coherence_score` | FLOAT | DEFAULT 0, [0,1] | 叙事自洽度 |
| `last_calibrated_at` | TIMESTAMPTZ | — | 最后外部校准时间 |
| `calibration_count` | INTEGER | DEFAULT 0 | 累计校准次数 |
| `anchor_version` | INTEGER | DEFAULT 1 | 见证锚定版本号 |
| `overridden_by_external` | BOOLEAN | DEFAULT FALSE | 是否曾被外部校准覆盖 |

### usage_weight（使用权重影子副本）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `memory_id` | UUID | PK, FK → memories(id) | 对应记忆 |
| `usage_count` | INTEGER | DEFAULT 0 | 累计使用次数 |
| `last_used_at` | TIMESTAMPTZ | — | 最后使用时间 |
| `activation_weight` | FLOAT | DEFAULT 0, [0,1] | 当前激活权重 |
| `use_load_retrieval` | FLOAT | DEFAULT 0 | 检索级负载系数 |
| `use_load_verification` | FLOAT | DEFAULT 0 | 验证级负载系数 |
| `use_load_contribution` | FLOAT | DEFAULT 0 | 贡献级负载系数 |
| `use_load_simulation` | FLOAT | DEFAULT 0 | 模拟级负载系数 |
| `use_load_implicit` | FLOAT | DEFAULT 0 | 内隐级负载系数 |
| `exploration_confidence` | FLOAT | DEFAULT 0, [0,1] | 探索置信度（探索产物专用） |
| `suspect_flag` | BOOLEAN | DEFAULT FALSE | 存疑标记（差异检验未通过） |

---

## 三、使用事件表

### usage_events（使用事件总线持久化）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | BIGSERIAL | PK | |
| `event_type` | TEXT | NOT NULL | 枚举见 §8.8 事件类型 |
| `source_layer` | TEXT | NOT NULL | 来源层 |
| `memory_id` | UUID | FK → memories(id) | 关联记忆 |
| `context` | JSONB | — | 事件上下文 |
| `severity` | INTEGER | DEFAULT 0, [0,9] | 事件优先级 |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `ttl` | INTERVAL | — | 生存时间，到期自动清理 |

**分区**：按 `created_at` 时间分区（月/季），过期分区自动归档或删除。

---

## 四、调度与状态表

### sublimation_queue（升华队列）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `memory_id` | UUID | FK → memories(id) | 被升华的记忆 |
| `stage` | TEXT | NOT NULL | raw / item / strategy / behavior |
| `status` | TEXT | NOT NULL | pending / processing / completed / failed / awaiting_approval |
| `output` | TEXT | — | 升华产物 |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `completed_at` | TIMESTAMPTZ | — | |

### forgetting_queue（遗忘队列）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `memory_id` | UUID | FK → memories(id) | 被遗忘候选 |
| `forgetting_score` | FLOAT | NOT NULL, [0,1] | 遗忘得分 |
| `reason` | TEXT | — | 触发原因 |
| `status` | TEXT | NOT NULL | pending_archive / archived / revoked |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

---

## 五、审计表

### audit_log（审计日志）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | BIGSERIAL | PK | |
| `timestamp` | TIMESTAMPTZ | NOT NULL | |
| `operator` | TEXT | NOT NULL | 操作者身份 |
| `action` | TEXT | NOT NULL | 操作类型 |
| `target_type` | TEXT | — | 目标类型（memory/config/user/redline） |
| `target_id` | TEXT | — | 目标 ID |
| `content_hash` | TEXT | — | 操作内容的 SHA-256 |
| `previous_hash` | TEXT | — | 上一条审计日志的 HMAC |
| `hmac` | TEXT | NOT NULL | HMAC-SHA256 签名 |
| `details` | JSONB | — | 详细信息 |
| `redline_id` | TEXT | — | 触发的安全红线编号（如有） |

**审计链完整性**：`hmac = HMAC-SHA256(hmac_key, timestamp || operator || action || content_hash || previous_hash)`

---

## 六、配置表

### config（运行时配置）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `key` | TEXT | PK | 配置键 |
| `value` | TEXT | NOT NULL | 配置值 |
| `scope` | TEXT | DEFAULT 'static' | static / dynamic / override |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_by` | TEXT | — | 更新者 |

### seeds（种子锚点）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `path` | TEXT | NOT NULL, UNIQUE | `kairos://_system/seeds/{name}` |
| `seed_type` | TEXT | NOT NULL | config / identity / calibration |
| `initial_confidence` | FLOAT | NOT NULL, [0,1] | 初始置信度 |
| `current_confidence` | FLOAT | NOT NULL, [0,1] | 当前衰减后置信度 |
| `degradation_level` | FLOAT | DEFAULT 0, [0,1] | 退化程度（0=新种子，1=完全退化） |
| `status` | TEXT | NOT NULL, DEFAULT 'active' | active / degrading / retired |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `last_reviewed_at` | TIMESTAMPTZ | — | 最近一次适配性审查时间 |
| `review_count` | INTEGER | DEFAULT 0 | 累计审查次数 |
| `bias_reset_count` | INTEGER | DEFAULT 0 | 偏置重置次数 |
| `content_snapshot` | JSONB | — | 种子内容的定稿快照 |

---

## 版本记录

| 版本 | 日期 | 变更 |
|:----|:----|:-----|
| v1.0.0 | 2026-07-20 | 初始数据模型设计。11 张核心表（memories / memory_relations / memory_tags / witness_anchor / usage_weight / usage_events / sublimation_queue / forgetting_queue / audit_log / config / seeds）+ 索引定义。 |
