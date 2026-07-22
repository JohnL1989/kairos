---
title: Graphiti 对比分析与 Kairos 改造方案
aliases:
  - Graphiti Cross Analysis
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

# Graphiti 对比分析与 Kairos 改造方案

## 一、项目概要

### Graphiti v0.29.2（Zep）

| 属性 | 值 |
|:----|:----|
| 定位 | **时序上下文图谱引擎**——为 AI Agent 构建随时间演化的知识图谱 |
| 技术栈 | Python + Neo4j/FalkorDB/Neptune/Kuzu + ArXiv 论文 |
| 规模 | **29k stars**, 895 commits, ArXiv 2501.13956, 196 releases |
| 核心创新 | Episode → Entity/Fact → Community 三级知识流水线 + 时序有效窗 + 增量构建 |
| 设计哲学 | **追踪事实的时间线，而非仅存储最新状态** |

---

## 二、Kairos 已有覆盖

| Graphiti | Kairos 对应 | 状态 |
|:---------|:------------|:-----|
| 实体节点 + 摘要演化 | entities 表 + 实体知识图谱 | ✅ §5.2 |
| 关系三元组 + 时序窗口 | memory_entities(valid_from/valid_to/superseded_by) | ✅ data-model |
| Episode → 实体提取 | 升华管道 + 实体提取（Deep 模式） | ✅ §5.2 |
| 增量构建 | 加工区 + 后台维护 | ✅ §5.2/§5.10 |
| 混合检索（语义+BM25+图遍历） | 5D 混合排序 + 递归 CTE 图遍历 | ✅ §7.3 |
| Cross-encoder 重排序 | 可选 cross-encoder 重排序 | ✅ §7.3 |
| 时序查询 | as_of / timeline / invalidate / supersede | ✅ §5.2 |
| 自定义实体类型（Pydantic） | 实体类型约束 | ✅ |
| MCP 服务器 | MCP Bridge 12 工具 | ✅ §7.3 |
| 事实自动失效（invalidation） | fact_freshness 过期扫描 | ✅ §5.2 |

### Graphiti 独有的设计

| 特性 | 说明 | 差距 |
|:-----|:------|:------|
| **社区检测（Community Detection）** | 将紧密关联的实体群聚为社区，支持社区级检索和摘要——"GraphRAG 风格"的高层上下文 | **▲ 值得吸收** |
| **图谱距离重排序** | 检索结果按图谱距离（实体间最短路径）重新排序——图谱上越近的结果越相关 | **▲ 值得吸收** |
| **可插拔图后端** | Neo4j/FalkorDB/Neptune/Kuzu 可互换 | ○ Kairos 计划评估 Apache AGE |

---

## 三、Kairos 改造方案

### P0：社区检测（Community Detection）

**当前**：Kairos 的实体知识图谱支持单跳和多跳图遍历，但缺少实体群的自动聚类——无法回答"这些实体属于哪些主题域"。

**改造**：在后天维护 Deep 模式中增加社区检测步骤——

**方法**：
1. 以 entities 表 + memory_entities 表为输入，按关系边构建无向图
2. 使用 Label Propagation 算法（可扩展至 Leiden/Louvain）检测社区
3. 每个社区生成社区摘要（聚合社区内实体的名称、类型分布、关键关系）
4. 社区结果写入 `entity_communities` 表

**新增表 `entity_communities`**：

| 列名 | 类型 | 说明 |
|:-----|:-----|:------|
| id | UUID PK | |
| community_label | TEXT | 社区标签（自动生成） |
| member_entity_ids | UUID[] | 成员实体 ID 列表 |
| summary | TEXT | 社区摘要（LLM 生成） |
| detection_algorithm | TEXT | label_propagation / leiden / manual |
| confidence | FLOAT | 检测置信度 |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**消费方式**：
- 检索时可附带 `community_id` 参数，将检索范围限定到某个社区
- 社区摘要可作为高层上下文注入——避免检索分散在多个不相关的实体群中
- 后台维护 Deep 模式每次执行时重新检测，增量更新已有社区

**配置参数**：`KAIROS_COMMUNITY_DETECTION_ENABLED`（默认 true），`KAIROS_COMMUNITY_DETECTION_ALGORITHM`（默认 label_propagation），`KAIROS_COMMUNITY_MIN_SIZE`（默认 3）

### P1：图谱距离重排序

**当前**：Kairos 的检索排序使用 5D 混合打分 + 可选 cross-encoder 重排——没有考虑候选结果在图谱中的相互距离。

**改造**：在 5D 排序后增加可选的重排序信号——查询的实体在图谱中的邻近实体优先排序。

**实现**：
1. 对查询执行实体识别，找到查询关联的实体集合 Q
2. 对每个候选结果 R，计算 R 的实体到 Q 的最短图谱距离
3. 图谱距离得分 = 1 / (1 + min_distance)——距离越近得分越高
4. 图谱距离得分作为额外的排序信号，以权重 `w_graph`（默认 0.15）加入 5D 混合排序

**配置参数**：`KAIROS_GRAPH_DISTANCE_ENABLED`（默认 true），`KAIROS_GRAPH_DISTANCE_WEIGHT`（默认 0.15），`KAIROS_GRAPH_DISTANCE_MAX_HOPS`（默认 3）
