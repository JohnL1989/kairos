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
updated: 2026-07-23
status: draft
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
| `path` | TEXT | NOT NULL, UNIQUE(path, version) | kairos:// 路径。同路径多条记忆通过递增 version 写入（首次写入 version=1，后续写入 version 递增） |
| `version` | INTEGER | DEFAULT 1 | 版本号，更新时递增 |
| `content` | TEXT | NOT NULL | 记忆内容 |
| `content_summary` | TEXT | — | 记忆摘要（由升华管道生成，用于 RL1 中层检索。v1.0 统一 1536 维单向量；128 维摘要向量与 2048 维全量向量为 v1.1+ 检索深度分级目标，见架构 §3.9） |
| `content_hash` | TEXT | NOT NULL | SHA-256(content) |
| `embedding` | VECTOR(1536) | —（向量检索时 NULL 记录被自动跳过） | 语义向量。标准模式 1536 维（text-embedding-3-small）；轻量模式 1536 维（BGE-M3，原生 1024 维线性投影至 1536），DDL 以 1536 为准 |
| `memory_types` | JSONB | NOT NULL | JSON 数组：["episodic", "narrative", "semantic", "procedural"] 可组合，一条记忆可同时属于多类型 |
| `contract` | TEXT | NOT NULL, DEFAULT 'ondemand' | 契约类型：permanent / ondemand / environmental / temporary（临时契约写回 LTM 带 TTL，到期自动清除） |
|| `hall` | TEXT | DEFAULT 'processing' | 知识加工区：processing / validation / canonical |
|| `solution_branch_id` | UUID | — | 所属解决方案分支 ID（同一记忆的多种语境化表征） |
|| `distill_level` | INTEGER | DEFAULT 0, [0,4] | 蒸馏层级：0=碎片 / 1=会话 / 2=日总结 / 3=体系 / 4=元规则 |
|| `extinction_status` | TEXT | DEFAULT 'active' | 知识灭绝状态：active / extinct（已灭绝）/ fossilized（已化石化） |
|| `extinct_at` | TIMESTAMPTZ | — | 灭绝时间（extinction_status=extinct 时设置） |
|| `extinct_reason` | TEXT | — | 灭绝触发事件描述（外部环境变更记录） |
|| `lma_urn` | TEXT | — | 逻辑记忆地址 URN（MTL 二层映射的永久逻辑地址，格式：urn:kairos:lma:<uuid>），首次写入时分配，物理迁移不变 |
| `sync_version` | INTEGER | DEFAULT 0 | 端云同步本地版本号 |
| `provenance` | TEXT | NOT NULL | 来源：external_calibration / internal_inference / user_input / system_generated / exploration |
| `status` | TEXT | NOT NULL, DEFAULT 'active' | active / stale / archived / suppressed / superseded。`suppressed` 为 `archived` 子态（被抑制路径不可检索，数据仍存在） |
| `is_identity` | BOOLEAN | DEFAULT FALSE | 是否为身份记忆 |
| `is_structure` | BOOLEAN | DEFAULT FALSE | 是否为结构性记忆（认知完整性轴） |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | 软删除标记，API 软删除操作设置此标记（保留审计痕迹） |
| `calibration_confidence` | FLOAT | DEFAULT 0.5, [0,1] | 校准置信度 |
| `vad_v` | FLOAT | DEFAULT 0, [-1,1] | 情感效价（Valence） |
| `vad_a` | FLOAT | DEFAULT 0, [-1,1] | 情感唤醒度（Arousal） |
| `vad_d` | FLOAT | DEFAULT 0, [-1,1] | 情感支配度（Dominance） |
| `decontextualization_level` | FLOAT | DEFAULT 0, [0,1] | 去语境化程度，升华时递增 |
| `heat_score` | FLOAT | DEFAULT 1.0, [0,1] | 热度评分，用于排序权重调制 |
| `expires_at` | TIMESTAMPTZ | — | 临时契约自动清除时间（仅 temporary 契约有效，到期后台清除） |
| `encoding_context` | JSONB | — | 编码情境（时空上下文/任务目标/关联记忆ID） |
| `created_at` | TIMESTAMPTZ | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMPTZ | NOT NULL | 最后更新时间 |
| `superseded_by` | UUID | REFERENCES memories(id) ON DELETE SET NULL | 被取代的新记忆 ID（修正场景）。注意：临时契约硬删除时该 FK 自动置 NULL |
| `last_access_at` | TIMESTAMPTZ | — | 最后访问时间（用于遗忘曲线计算） |
| `domain` | TEXT | DEFAULT 'general' | 领域标签（用于领域路由检索） |

**索引**：
- `idx_memories_path` ON `path`（支持前缀查询）
- `idx_memories_contract` ON `contract`
| `idx_memories_types` ON `memory_types`（JSON 数组索引，使用 GIN）
- `idx_memories_created` ON `created_at`
- `idx_memories_identity` ON `is_identity` WHERE `is_identity = TRUE`
- `idx_memories_status` ON `status`
| `idx_memories_last_access` ON `last_access_at`
| `idx_memories_hall_status` ON `hall`, `status`
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
**约束**：UNIQUE(source_id, target_id, relation_type) 防止同一对记忆之间的同类型关系重复插入。

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
| `event_type` | TEXT | NOT NULL | 枚举见架构 §10.10 事件类型枚举 |
| `source_layer` | TEXT | NOT NULL | 来源层 |
| `memory_id` | UUID | FK → memories(id) | 关联记忆 |
| `context` | JSONB | — | 事件上下文 |
| `severity` | INTEGER | DEFAULT 0, [0,9] | 事件严重级别 |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `ttl` | INTERVAL | — | 生存时间，到期自动清理 |

**分区**：按 `created_at` 时间分区（月/季），过期分区自动归档或删除。

**建议索引**：`(memory_id, created_at)` — 遗忘调度器的 `WHERE memory_id = X AND created_at > NOW - 30d` 查询依赖此索引

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

**审计链完整性**：`hmac = HMAC-SHA256(hmac_key, timestamp | operator | action | target_type | target_id | content_hash | details | previous_hash)`

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

### sublimation_outputs（升华输出表，v1.0 新增）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | UUID | PK | |
| `memory_id` | UUID | FK → memories(id) | 被升华的记忆 |
| `stage` | TEXT | NOT NULL | raw / item / strategy / behavior |
| `output_type` | TEXT | NOT NULL | pattern / rule / insight / preference |
| `content` | TEXT | NOT NULL | 升华产物内容 |
| `confidence` | FLOAT | NOT NULL, [0,1] | 置信度（< SUBLIMATION_CONFIDENCE_FLOOR 不回写） |
| `status` | TEXT | NOT NULL, DEFAULT 'pending_review' | pending_review / approved / rejected / discarded |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

### memory_states（记忆状态转换跟踪表）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | BIGSERIAL | PK | |
| `memory_id` | UUID | NOT NULL | 关联 memories.id |
| `memory_type` | TEXT | NOT NULL | 记忆过程分类（映射至 storage/knowledge/experience/task）：knowledge=语义类（semantic），experience=情景类（episodic+narrative），task=程序类（procedural）。与 `memories.memory_types` 的多重认知分类（episodic/narrative/semantic/procedural）为不同分类轴——memory_type 是存储内部的过程管理分类，memory_types 是认知模型的记忆类型标记。两者映射关系：knowledge↔semantic，experience↔episodic+narrative，task↔procedural |
| `state` | TEXT | NOT NULL | active / stale / archived / suppressed / superseded |
| `previous_state` | TEXT | DEFAULT '' | 转换前状态 |
| `state_changed_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| `reason` | TEXT | DEFAULT '' | 转换原因 |
| `source` | TEXT | DEFAULT 'system' | 触发源 |

**约束**：无 UNIQUE 约束——支持同一记忆多次状态转换（保留完整历史）。
**索引**：INDEX(memory_id, state_changed_at) 加速历史查询

### knowledge_evolution（知识演化追踪表）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | BIGSERIAL | PK | |
| `source_id` | UUID | NOT NULL | 源记忆 ID（FK → memories.id） |
| `target_id` | UUID | NOT NULL | 目标记忆 ID（FK → memories.id） |
| `relation_type` | TEXT | NOT NULL | replaces / enriches / confirms / challenges |
| `confidence` | FLOAT | DEFAULT 0.5 | 检测置信度 |
| `detection_method` | TEXT | DEFAULT 'jaccard' | jaccard / llm / manual |
| `reason` | TEXT | DEFAULT '' | 检测原因 |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |


### journal_entries（升华原始轮次表，v1.0 新增）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | BIGSERIAL | PK | |
| `session_id` | TEXT | NOT NULL | 所属会话 |
| `role` | TEXT | NOT NULL | user / assistant / tool |
| `content` | TEXT | NOT NULL | 原始内容 |
| `source` | TEXT | — | 来源标识 |
| `platform` | TEXT | — | 平台标签 |
| `filtered` | BOOLEAN | DEFAULT FALSE | 是否被捕获门控过滤 |
| `captured_at` | TIMESTAMPTZ | NOT NULL | |

### session_summaries（L1 会话摘要表，v1.0 新增）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | UUID | PK | |
| `session_id` | TEXT | NOT NULL, UNIQUE | |
| `user_id` | TEXT | NOT NULL | |
| `summary` | TEXT | — | 会话摘要 |
| `key_decisions` | JSONB | — | 关键决策列表 |
| `entities` | JSONB | — | 提取的实体列表 |
| `heat_score` | FLOAT | DEFAULT 1.0 | 热度评分 |
| `token_count` | INTEGER | DEFAULT 0 | |
| `start_time` | TIMESTAMPTZ | — | |
| `end_time` | TIMESTAMPTZ | — | |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `ttl_days` | INTEGER | DEFAULT 30 | 保留天数 |

### daily_reports（L2 日报告表，v1.0 新增）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | UUID | PK | |
| `user_id` | TEXT | NOT NULL | |
| `report_date` | DATE | NOT NULL | |
| `summary` | TEXT | — | 日摘要 |
| `insights` | JSONB | — | 当日洞察列表 |
| `session_count` | INTEGER | DEFAULT 0 | 当日会话数 |
| `decision_count` | INTEGER | DEFAULT 0 | 关键决策数 |
| `heat_score` | FLOAT | DEFAULT 1.0 | |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| UNIQUE(user_id, report_date) | | | |

### weekly_packs（L3 周知识包表，v1.0 新增）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | UUID | PK | |
| `user_id` | TEXT | NOT NULL | |
| `week_start` | DATE | NOT NULL | |
| `patterns` | JSONB | — | 识别到的模式列表 |
| `trends` | JSONB | — | 趋势分析 |
| `key_decisions` | JSONB | — | 本周关键决策 |
| `session_ids` | UUID[] | — | 归属于本周的会话 UUID（引用外部系统会话 ID，非本系统 PK） |
| `heat_score` | FLOAT | DEFAULT 1.0 | |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| UNIQUE(user_id, week_start) | | | |

### user_profiles（L4 用户画像表，v1.0 新增）

用户画像分**静态（static）**与**动态（dynamic）**两层——静态层记录长期稳定事实（偏好、身份、特质），数据来自 L4 profile 的跨周聚合；动态层记录近期活动和当前上下文（正在进行的任务、最近对话主题），数据来自 L1→L3 增量更新。两层共享同一张表，通过 `trait_type`（static/dynamic）区分。检索时静态层权重高于动态层。

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `user_id` | TEXT | NOT NULL | 用户 ID（复合 PK 的一部分） |
| `trait_type` | TEXT | NOT NULL, DEFAULT 'dynamic' | static（长期稳定）/ dynamic（近期活动），见上文说明。复合主键：PRIMARY KEY (user_id, trait_type) |
| `preferences` | JSONB | DEFAULT '{}' | 用户偏好 |
| `traits` | JSONB | DEFAULT '{}' | 用户特征 |
| `skill_summaries` | JSONB | DEFAULT '{}' | 技能摘要 |
| `confidence` | FLOAT | DEFAULT 0.5 | 画像置信度 |
| `version` | INTEGER | DEFAULT 1 | 画像版本号 |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |
| `rl_weights` | JSONB | — | RL 权重六维配置：键为 `relevance`/`recency`/`frequency`/`explicit_feedback`/`entity_boost`/`trust_score`，各维独立取值，不强制和为 1（各维度独立更新，见 rl-weight-spec.md 初始化说明）。v1.0 entity_boost 默认 0.05 不主动参与排序，v1.1+ 激活完整加权 |

## 七、扩展表

### conversation_messages（对话消息持久化）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | BIGSERIAL | PK | |
| `session_id` | TEXT | NOT NULL | Hermes 会话 ID |
| `role` | TEXT | NOT NULL | user / assistant / tool |
| `content` | TEXT | — | 消息内容 |
| `tool_call_id` | TEXT | — | 工具调用 ID |
| `tool_calls` | JSONB | — | 工具调用参数 |
| `tool_name` | TEXT | — | 工具名 |
| `timestamp` | FLOAT | NOT NULL | 时间戳 |
| `token_count` | INTEGER | — | Token 计数 |
| `finish_reason` | TEXT | — | 完成原因 |
| `reasoning` | TEXT | — | 推理过程 |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |

**索引**：
- `idx_conv_session` ON `session_id`（支持按会话查询）
- `idx_conv_timestamp` ON `timestamp`

### entities（实体知识图谱）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | BIGSERIAL | PK | |
| `user_id` | TEXT | NOT NULL | |
| `name` | TEXT | NOT NULL | 实体名称 |
| `type` | TEXT | DEFAULT 'concept' | project / people / concept / tool |
| `description` | TEXT | — | 实体描述 |
| `embedding` | VECTOR(1536) | —（向量检索时 NULL 记录被自动跳过） | 语义向量。标准模式 1536 维（text-embedding-3-small）；轻量模式 1536 维（BGE-M3，原生 1024 维线性投影至 1536），DDL 以 1536 为准 |
| `metadata` | JSONB | — | 扩展元数据 |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |
| UNIQUE(user_id, name) | | | |

### memory_entities（记忆-实体关联）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | BIGSERIAL | PK | |
| `memory_id` | UUID | FK → memories(id) | 关联记忆 |
| `entity_id` | BIGINT | FK → entities(id) | 关联实体 |
| `relation` | TEXT | DEFAULT 'mentions' | 关系类型 |
| `valid_from` | TIMESTAMPTZ | — | 关系有效起始（NULL=不绑定时间） |
| `valid_to` | TIMESTAMPTZ | — | 关系有效截止（NULL=当前有效） |
| `superseded_by` | BIGINT | — | 被替代关系 FK → memory_entities(id) |
| UNIQUE(memory_id, entity_id, valid_from) | | 时序版本化：同一 memory↔entity 对可随时间有效多条关系 |

### memory_chunks（长文本分块索引）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | BIGSERIAL | PK | |
| `memory_id` | UUID | FK → memories(id), ON DELETE CASCADE | 父记忆 |
| `chunk_index` | INTEGER | NOT NULL | 块序号 |
| `content` | TEXT | NOT NULL | 块内容 |
| `text_hash` | TEXT | — | SHA256(content)，用于差分同步比较 |
| `embedding` | VECTOR(1536) | —（向量检索时 NULL 记录被自动跳过） | 语义向量。标准模式 1536 维（text-embedding-3-small）；轻量模式 1536 维（BGE-M3，原生 1024 维线性投影至 1536），DDL 以 1536 为准 |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |
| UNIQUE(memory_id, chunk_index) | | | |

### sync_queue（端云同步队列）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | BIGSERIAL | PK | |
| `memory_id` | UUID | FK → memories(id) | 待同步记忆 |
| `operation` | TEXT | NOT NULL | create / update / delete |
| `sync_direction` | TEXT | NOT NULL | upload / download |
| `sync_state` | TEXT | NOT NULL | pending / synced / conflict |
| `local_version` | INTEGER | NOT NULL | 本地版本号 |
| `remote_version` | INTEGER | — | 远端版本号 |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `synced_at` | TIMESTAMPTZ | — | |

### fact_freshness（事实新鲜度元数据）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | UUID | PK | |
| `subject_type` | TEXT | NOT NULL | 'memory' |
| `subject_id` | UUID | NOT NULL | 关联记忆 ID（FK → memories.id） |
| `fact_key` | TEXT | NOT NULL | 归一化事实键 |
| `truth_type` | TEXT | NOT NULL | factual / project_fact / environment_fact |
| `validator_kind` | TEXT | DEFAULT 'none' | none / file_exists / command / http / manual |
| `validator_spec` | JSONB | — | 验证参数（命令/URL等） |
| `ttl_days` | INTEGER | DEFAULT 0 | TTL 天数 |
| `last_checked_at` | TIMESTAMPTZ | — | 最后检查时间 |
| `valid_until` | TIMESTAMPTZ | — | 有效期截止 |
| `status` | TEXT | DEFAULT 'needs_live_check' | current / expired / stale / superseded / needs_live_check |
| `stale_reason` | TEXT | DEFAULT '' | |
| `superseded_by` | TEXT | DEFAULT '' | |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | |

### procedural_playbooks（过程知识 Playbook）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | TEXT | PK | `pb_{uuid}` |
| `scope_id` | TEXT | NOT NULL | |
| `shared_scope_id` | TEXT | — | |
| `task_class` | TEXT | NOT NULL | |
| `title` | TEXT | NOT NULL | |
| `trigger` | TEXT | — | |
| `goal` | TEXT | — | |
| `preconditions` | JSONB | DEFAULT '[]' | |
| `steps` | JSONB | NOT NULL | `[{number, capability_class, action, evidence_required, why, previous_mistakes}]` |
| `pitfalls` | JSONB | DEFAULT '[]' | |
| `verification` | JSONB | DEFAULT '[]' | |
| `cleanup` | JSONB | DEFAULT '[]' | |
| `evidence_anchors` | JSONB | DEFAULT '[]' | |
| `related_skills` | JSONB | DEFAULT '[]' | |
| `environment_constraints` | JSONB | DEFAULT '{}' | |
| `reuse_policy` | JSONB | DEFAULT '{}' | |
| `status` | TEXT | DEFAULT 'candidate' | candidate / needs_review / reviewed / promoted / superseded |
| `confidence` | FLOAT | DEFAULT 0.5 | |
| `success_count` | INTEGER | DEFAULT 0 | |
| `failure_count` | INTEGER | DEFAULT 0 | |
| `stale_count` | INTEGER | DEFAULT 0 | |
| `created_from_episode_id` | TEXT | — | |
| `superseded_by` | TEXT | — | |
| `last_used_at` | TIMESTAMPTZ | — | |
| `last_verified_at` | TIMESTAMPTZ | — | |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | |
| `metadata` | JSONB | DEFAULT '{}' | |

### procedural_playbooks_fts（Playbook 全文索引）

| 列名 | 类型 | 说明 |
|:----|:-----|:-----|
| `playbook_id` | TEXT | FK → procedural_playbooks(id) |
| `title` | TEXT | |
| `trigger` | TEXT | |
| `goal` | TEXT | |
| `preconditions` | TEXT | |
| `steps` | TEXT | |
| `pitfalls` | TEXT | |
| `verification` | TEXT | |

### playbook_versions（Playbook 版本历史）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | TEXT | PK | |
| `playbook_id` | TEXT | FK → procedural_playbooks(id) | |
| `version` | INTEGER | NOT NULL | |
| `change_type` | TEXT | NOT NULL | create / review / promote / supersede / feedback |
| `change_reason` | TEXT | — | |
| `snapshot` | JSONB | — | 完整 playbook 快照 |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |

### entity_communities（实体社区）

| 列名 | 类型 | 约束 | 说明 |
|:----|:-----|:-----|:-----|
| `id` | UUID | PK | |
| `community_label` | TEXT | NOT NULL | 社区标签（自动生成） |
| `member_entity_ids` | UUID[] | NOT NULL | 成员实体 UUID 列表（引用外部系统实体，非本系统 PK） |
| `summary` | TEXT | — | 社区摘要（LLM 生成） |
| `detection_algorithm` | TEXT | DEFAULT 'label_propagation' | label_propagation / leiden / manual |
| `confidence` | FLOAT | DEFAULT 0.5 | |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | |

---

## 八、解决方案谱系与知识灭绝

### solution_branches（解决方案分支表）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | 分支全局唯一 ID |
| `root_memory_id` | UUID | FK → memories(id) | 所属原始记忆 ID |
| `branch_name` | TEXT | NOT NULL | 分支名称（如 concise / detailed / step_by_step） |
| `context_signature` | TEXT | — | 触发此分支的上下文特征（哈希或摘要） |
| `usage_count` | INTEGER | DEFAULT 0 | 分支被检索次数 |
| `last_used_at` | TIMESTAMPTZ | — | 分支最后使用时间 |
| `status` | TEXT | DEFAULT 'active' | active / dormant（休眠）/ merged（已合并） |
| `merged_into` | UUID | — | 合并目标分支 ID |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

**约束**：UNIQUE(root_memory_id, branch_name)

### extinction_fossils（知识化石表）

| 列名 | 类型 | 约束 | 说明 |
|:----|:----|:----|:-----|
| `id` | UUID | PK | |
| `original_memory_id` | UUID | FK → memories(id) | 原记忆 ID（保留关联） |
| `content_hash` | TEXT | NOT NULL | 原始内容的 SHA-256 哈希（替代原文） |
| `path` | TEXT | NOT NULL | 原路径（保留用于拓扑恢复） |
| `extinct_at` | TIMESTAMPTZ | NOT NULL | 灭绝时间 |
| `extinct_reason` | TEXT | NOT NULL | 灭绝原因（外部环境变更描述） |
| `restore_condition` | TEXT | — | 恢复条件描述（如「pgvector 版本 >= 0.7.0」） |
| `related_fossil_ids` | UUID[] | — | 关联化石 ID 列表（同一灭绝事件链） |

## 九、注册表结构

注册表不是 SQL 表，而是由编译器维护的树形键值对空间。其逻辑结构如下：

| 根键 | 路径 | 值类型 | 写入权限 | 说明 |
|:----|:----|:------|:--------|:-----|
| HKLA | identity/agent_name | TEXT | 初始化 | Agent 显示名称 |
| HKLA | identity/agent_id | UUID | 初始化 | Agent 全局唯一 ID |
| HKLA | soul/core_tone | ENUM | 宪法修订端口 | 核心语气（professional/concise/friendly） |
| HKCU | profile/name | TEXT | 编译器 | 当前用户名称 |
| HKCU | preferences/code_style | TEXT | 编译器 | 代码风格偏好 |
| HKLM | hardware/cpu/cores | INTEGER | 系统 | CPU 核心数 |
| HKLM | network/status | ENUM | 系统 | 网络状态（online/offline/restricted） |
| HKCS | current_task/id | UUID | 编译器 | 当前任务 ID |
| HKCS | current_task/phase | TEXT | 编译器 | 当前任务阶段 |
## 版本记录

| 版本 | 日期 | 说明 |
|:----|:----|:-----|
| v1.0.0 | 2026-07-23 | 数据模型设计定稿（文档仍保持 draft 状态——无运行代码验证）。核心记忆表 30+ 字段（新增 content_summary 摘要列；含 hall 知识加工区标识、calibration_confidence 校准置信度、VAD 情感三维、encoding_context 编码情境）。扩展字段：solution_branch_id（谱系分支）、distill_level（蒸馏层级 0-4）、extinction_status（灭绝状态）、lma_urn（MTL 逻辑地址）。双副本分离：witness_anchor 见证锚定表（含叙事自洽度/校准历史）与 usage_weight 使用权重表（含五级负载系数）。新增表：solution_branches、extinction_fossils、memory_relations、entity_communities 等（注：vector_collections 与 community_detection 为早期命名，实际对应实体嵌入直接存储于 memories.embedding 列，社区发现使用 entity_communities 表）。注册表逻辑结构（九类根键/路径/值类型/写入权限定义）。v1.0 统一 1536 维单向量，128/2048 为 v1.1+ 目标（见架构 §3.9）。user_profiles 新增 rl_weights 列，承载六维 RL 权重配置（见 rl-weight-spec.md）。 |
