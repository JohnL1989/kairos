---
title: MemPalace 对比分析与 Kairos 改造方案
aliases:
  - MemPalace Cross Analysis
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

# MemPalace 对比分析与 Kairos 改造方案

## 一、项目概要

### MemPalace v3.6.0

| 属性 | 值 |
|:----|:----|
| 定位 | 本地优先的 AI 记忆系统——原文存储，可插拔后端 |
| 技术栈 | Python + ChromaDB/SQLite/Milvus/Qdrant/pgvector + SQLite KG |
| 规模 | **57.6k stars**, 1,529 commits, v3.6.0 |
| 核心创新 | 96.6% R@5 raw on LongMemEval、Wing/Room/Drawer 结构、RFCD 规范 001 后端契约、时序知识图谱 |
| 设计哲学 | **原文存储，不汇总、不提取、不改写** |

### MemPalace 回答的根本问题

> **在"不依赖任何 LLM API"的前提下，如何达到最高的检索召回率？**

它用纯语义搜索（无启发式、无 LLM）实现 96.6% R@5。混合管道（+关键字提升 + 时间邻近 + 偏好提取）推到 98.4%。

---

## 二、核心差异分析

### 2.1 MemPalace 有而 Kairos 无的独特设计

| 特性 | MemPalace | Kairos | 差距 |
|:-----|:----------|:-------|:-----|
| **时序知识图谱** | 实体关系三元组 + `valid_from/valid_to` + `as_of` 时间查询 + `invalidate`/`supersede` | 实体知识图谱 + `knowledge_evolution` 表，无显式时序窗 | **▲ 值得吸收** |
| **RFC 001 后端契约** | 完整 ABC 规范 + 类型化 QueryResult + embedder identity 检查 | 无统一后端接口定义 | 理念差异 |
| **原文存储** | 不总结、不提取、不改写 | 5D 混合排序 + 多维信号 | 定位不同 |
| **Auto-save hooks** | Claude Code + Codex CLI + Cursor IDE | 仅 Hermes | P2 |

### 2.2 值得借鉴的设计

| 理念 | 说明 |
|:-----|:------|
| **时序知识图谱** | 实体关系三元组带 `valid_from/valid_to` 窗口，支持 `as_of` 时间点查询——问"2026年1月时 Max 在做什么？"而不是"Max 做过什么？" |
| **Embedder identity 强制执行** | 在集合打开时检查存储的嵌入器身份 vs 当前嵌入器，模型不匹配则报错——防止模型替换后检索质量无声退化 |

---

## 三、Kairos 改造方案

### P0：时序知识图谱增强

**当前**：Kairos 有实体知识图谱（entities + memory_entities 表），知识演化追踪（knowledge_evolution 四类关系），以及 fact_freshness 表。但实体关系没有时间窗口，无法回答"在某个时间点，这个事实是否成立"。

**改造**：在实体知识图谱的基础上，增加时序能力：

**现有实体知识图谱**（entities + memory_entities）：
- 节点：entities 表（已有的）
- 边：memory_entities（已有的，含 relation_type）
- 时序窗口：新增 `valid_from` / `valid_to` 列到 memory_entities 表

**改造变更**：

```diff
 memory_entities 表
+  valid_from    TIMESTAMPTZ  — 关系有效起始（可选）
+  valid_to     TIMESTAMPTZ  — 关系有效截止（可选；NULL = 当前有效）
+  superseded_by TEXT        — 被哪条关系替代（FK → memory_entities.id）
```

新增查询能力：
- `as_of(timestamp)` — 查询在指定时间点有效的关系
- `timeline(entity_id)` — 返回指定实体所有关系的时间线（valid_from 升序）
- `invalidate(entity_a, relation, entity_b, at)` — 将指定关系标记为已失效（设 valid_to）
- `supersede(entity_a, relation, old_entity_b, new_entity_b, at)` — 同时关闭旧关系并创建新关系

**约束**：
- valid_from 和 valid_to 可同时为 NULL → 关系不绑定时间（行为同当前）
- valid_to < valid_from → 拒绝写入（反向间隔不可见）
- 时序窗口不影响检索排序——仅在 as_of 查询时过滤
- 后台维护 Deep 模式执行过期扫描——valid_to 在 30 天前的自动标记为 stale

---

## 四、不纳入的内容

| 特性 | 不纳入理由 |
|:-----|:-----------|
| **原文存储** | Kairos 结构包含升华管道、P6 维度保护——不是纯原文存储系统 |
| **RFC 001 后端契约** | Kairos 的存储抽象是 PostgreSQL/SQLite 双后端 + 多路径融合，不需要统一的向量后端接口 |
| **Wing/Room/Drawer** | Kairos 路径空间 `kairos://_user/_project/_session/_path` 已实现等价的层级隔离 |
| **Auto-save hooks** | P2，当前阶段聚焦文档和核心架构 |
| **Embedder identity 检查** | Kairos 的 embedding 后端未最终确定，identity 检查由具体实现负责 |
