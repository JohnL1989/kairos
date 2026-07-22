---
title: scope-recall 对比分析与 Kairos 改造方案
aliases:
  - Scope Recall Cross Analysis
tags:
  - kairos
  - analysis
  - comparison
  - design
created: 2026-07-22
status: merged-into-architecture
---

> **⚠️ 本文档为设计思考记录，所有内容已合并至 `architecture-v1.0.0.md`。**
> **开发请以 `architecture-v1.0.0.md` 为准，本文不保证与架构文档实时同步。**

# scope-recall 对比分析与 Kairos 改造方案

## 一、项目概要

### scope-recall v1.7.2

| 属性 | 值 |
|:----|:----|
| 定位 | Hermes 本地 current-turn recall + durable scoped memory provider |
| 技术栈 | Python + SQLite + LanceDB + FTS5 |
| 核心创新 | 三层架构（Journal→SQLite truth→Vector companion）、Scope 隔离模型、Experience playbook 系统、Freshness 元数据体系 |
| 运行形态 | Hermes MemoryProvider 插件 + 独立的 Hermes 包 |
| 成熟度 | v1.7.2，96 次提交，185 stars，39 个 release，完整 CI/CD |

---

## 二、四维对比分析

### 2.1 架构设计对比

| 维度 | scope-recall | Kairos | 优势 |
|:-----|:------------|:-------|:-----|
| **架构风格** | 3 层（Journal→SQLite truth→Vector companion） | 6 层 + 正交平面 | Kairos（理论深度） |
| **scope 模型** | 显式 shared/local 二分，cross-platform identity mapping | 路径前缀隔离（kairos://_user/_project/_session） | **▲ scope-recall（更工程化）** |
| **写入管线** | Turn→Journal→Digest→Durable memory | 写入→LTM（或加工区） | **▲ scope-recall（Journal 隔离）** |
| **存储引擎** | SQLite（truth）+ LanceDB/sqlite-bruteforce（vector） | PostgreSQL/SQLite + pgvector | ○ 各有优势 |
| **召回控制** | current-turn only，queue_prefetch 是 no-op | current-turn + 前瞻保持 | Kairos 更丰富 |
| **部署边界** | 本地 provider，export/import 桥接外部 | 后端服务 | ○ 定位不同 |

### 2.2 核心功能对比

| 功能 | scope-recall | Kairos | 差距 |
|:-----|:------------|:-------|:-----|
| **Scope 隔离** | 显式 shared/local 二分 + cross-platform identity mapping | 路径前缀隔离 | **▲ 值得吸收** |
| **Capture 过滤** | 12 种 skip pattern + secret regex + trivial detection + hard max | 摄取验证门禁 | **▲ 更全面** |
| **Journal 暂存** | Raw turns→journal→digest→durable（隔离写入与检索） | 对话历史持久化（纯存档） | **▲ 值得吸收** |
| **Freshness 元数据** | fact_freshness 表 + validator kinds + TTL + status + penalty | 遗忘调度器 + freshness | **▲ 结构化更好** |
| **Experience Playbook** | 完整过程知识生命周期（candidate→review→promoted→superseded） | 升华管道（raw→item→strategy→behavior） | **▲▲ 最大单项差距** |
| **Governance 工具** | dedupe/govern/hygiene/repair 全套操作工具 | 审计日志 + 宪法 | **▲ 值得吸收** |
| **Recall Funnel** | 每次查询的结构化 trace（stage counts/filters/timings） | 事件总线（通用） | **▲ 检索专属可观测性** |
| **Vector Repair** | rebuild + immutable generations + compare-and-swap | 无 | **▲** |
| **Hard Delete 安全** | fail-closed：需 vector store 才允许 SQLite delete | 软删除 | **▲ 安全实践** |
| **Process Knowledge FTS** | playbook 全文索引（steps/triggers/goals） | 记忆 FTS | **▲ playbook 专属** |
| **Cross-platform Identity** | user_aliases 映射 + canonical_user 元数据 | 无 | **▲** |

### 2.3 scope-recall 回答的根本问题

**「如何让 Agent 在当前对话中召回正确的记忆，同时在跨窗口场景下共享持久事实而不污染本地上下文？」**

它的两个核心设计原则：
1. **Current-turn only recall** — queue_prefetch() 是显式 no-op，彻底阻断话题漂移
2. **Shared vs Local 二分** — durable facts 可跨窗口，general scratch 严格隔离

---

## 三、Kairos 改造方案

### 需要改造的模块

| P | 模块 | 当前状态 | 改造方向 |
|:-|:-----|:---------|:---------|
| **P0** | **Capture 过滤** | 摄取门禁（基础过滤） | 增加 12 种 skip pattern + secret regex + trivial detection + hard_max + context marker 清理 |
| **P0** | **Experience Playbook 系统** | 无 | 新增完整过程知识生命周期 + FTS 全文检索 + 反馈循环 |
| **P1** | **Freshness 结构化** | 遗忘调度器 freshness | 新增 fact_freshness 表 + validator kinds + TTL + status + penalty 评分 |
| **P1** | **Recall Funnel** | 事件总线（通用） | 新增检索专属 trace：stage counts/filters/timings/scoring breakdown |
| **P2** | **Cross-platform Identity** | 无 | 新增 user_aliases 配置 + canonical_user 元数据 |
| **P2** | **Hard Delete 安全** | 软删除（无安全门） | fail-closed：hard delete 须先确认 vector 已清理 |

### 具体改造措施

#### P0-1：Capture 过滤增强

在 §7 接入层的摄取验证门禁中增加：

| 过滤模式 | 方法 | 说明 |
|:---------|:-----|:-----|
| Trivial 文本 | 预设词表匹配（ok/yes/thanks/收到/明白等 30+） | 拒绝写入 |
| 上下文标记 | `[Memory]`, `[SuperMemory]` 等 AI 标记清理 | 写入前剥离 |
| 秘密文本 | regex: `api_key`/`token`/`secret`/`password` + `:` + 值 | 拒绝写入 |
| 维护提示 | "review the conversation above"/"reply with ok" 等 | 拒绝写入 |
| 硬长度上限 | `KAIROS_CAPTURE_HARD_MAX_CHARS` 默认 4000 | 超限拒绝 |

#### P0-2：Experience Playbook 系统（新增子系统）

在存储层新增过程知识子系统——对应升华管道的 strategy→behavior 阶段的显式产物管理。

**Playbook 结构**：
```
ProceduralPlaybook:
  id, scope_id, task_class, title, trigger, goal
  preconditions[]
  steps[]: {number, capability_class, action, evidence_required, why, previous_mistakes[]}
  pitfalls[]
  verification[]
  cleanup[]
  reuse_policy: {frequency, confidence_threshold, allowed_contexts}
  status: candidate | needs_review | reviewed | promoted | superseded
  confidence: 0-1
  success_count, failure_count, stale_count
  related_skills[], evidence_anchors[], environment_constraints{}
```

**生命周期**：
- candidate（升华管道产出，待审查）→ needs_review（自动标记，需人工或宪法级确认）→ reviewed（审查通过但未推广）→ promoted（正式可用）→ superseded（被替代）

**存储**：`procedural_playbooks` 表 + `procedural_playbooks_fts` FTS5 表（对 title/trigger/goal/steps 建全文索引）+ `playbook_versions` 表

**Feedback**：每次使用后记录 outcome（success/partial/failed/stale/misleading），更新 success_count/failure_count/stale_count 和 confidence

**与升华管道的关系**：升华管道的 strategy 阶段产出 → Playbook candidate；behavior 阶段验证 → Playbook promoted

**配置参数**：`KAIROS_PLAYBOOK_DEFAULT_CONFIDENCE`=0.5, `KAIROS_PLAYBOOK_NEGATIVE_THRESHOLD`=3（连续 3 次 negative 自动降级）

#### P1-1：Freshness 结构化

新增 `fact_freshness` 表，与现有 `freshness` 计算联动：

| 列 | 类型 | 说明 |
|:---|:-----|:-----|
| id | UUID PK | |
| subject_type | TEXT | 'memory' |
| subject_id | TEXT | 对应记忆 ID |
| fact_key | TEXT | 归一化键 |
| truth_type | TEXT | factual/project_fact/environment_fact |
| validator_kind | TEXT | none/file_exists/command/http/manual |
| validator_spec | JSONB | 验证参数 |
| ttl_days | INTEGER | TTL |
| last_checked_at | TIMESTAMPTZ | |
| valid_until | TIMESTAMPTZ | |
| status | TEXT | current/expired/stale/superseded/needs_live_check |
| stale_reason | TEXT | |
| superseded_by | TEXT | |

`freshness_penalty(stale)=0.35, expired=0.28, needs_live_check=0.18` 作为检索排序的衰减系数。

#### P1-2：Recall Funnel

为每次检索请求记录结构化 trace：

```json
{
  "query": "...",
  "stages": {
    "lexical_candidates": 200,
    "vector_candidates": 150,
    "curated_candidates": 5,
    "merge_deduped": 280,
    "lifecycle_filtered": 250,
    "freshness_penalty": 0.15,
    "final_candidates": 10,
    "returned": 5
  },
  "timings_ms": {"total": 245, "lexical": 30, "vector": 180, "rerank": 35},
  "character_budget": 3000
}
```

trace 写入使用事件总线，标记 `recall_funnel`。对 `scope_recall_explain` 和 `scope_recall_benchmark` 模式返回完整 trace。

---

## 四、不纳入的内容

| 特性 | 不纳入理由 |
|:-----|:----------|
| **Journal 暂存层** | Kairos 已有加工区（Processing Zone）+ 对话历史持久化，功能等价——journal 是 SQLite 时代的设计，Kairos 的三区域模型更完善 |
| **Vector repair 工具** | Kairos 未确定 vector 后端，暂不定义 repair 接口 |
| **Governance dedupe 命令** | Kairos 的后台维护引擎 Deep 模式已含冗余合并 |
| **Cross-platform mapping** | P2，当前单用户场景优先级低 |

---

## 五、实施路线图

```
Phase 1（v1.0.x）：
  ├── Capture 过滤增强（12 种 skip pattern + secret regex + trivial + hard_max）
  └── Freshness 结构化（fact_freshness 表 + penalty 系数）

Phase 2（v1.1）：
  ├── Experience Playbook 系统（完整生命周期 + FTS + 反馈 + 版本追踪）
  └── Recall Funnel（检索 trace 结构化 + explain/benchmark 模式）

Phase 3（v1.2）：
  ├── Cross-platform Identity mapping
  └── Hard Delete fail-closed 安全门
```
