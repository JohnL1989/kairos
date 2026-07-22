---
title: MemOS 对比分析与 Kairos 改造方案
aliases:
  - MemOS Cross Analysis
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

# MemOS 对比分析与 Kairos 改造方案

## 一、项目概要

### MemOS v2.0 Stardust

| 属性 | 值 |
|:----|:----|
| 定位 | LLM/AI Agent 的记忆操作系统 |
| 技术栈 | Python (FastAPI) + TypeScript (local plugin) + Neo4j + Qdrant + SQLite |
| 规模 | 10.3k stars, 1,971 commits, 35 releases |
| 部署形态 | Cloud API + Self-host (Docker) + OpenClaw Plugin + Hermes Local Plugin |
| 核心创新 | Multi-Cube KB、三级技能进化（L1→L2→L3→Skills）、MemScheduler 异步摄取、图谱原生的记忆结构 |
| 论文 | ArXiv 2507.03724 |

### MemOS 回答的根本问题

> **Agent 如何在多会话、多用户、多工具的场景下，拥有结构化的持久记忆并能自我进化技能？**

它把记忆系统从「嵌入向量存储」提升为「可组织、可共享、可进化」的操作系统级能力。

---

## 二、核心差异分析

### 2.1 MemOS 有而 Kairos 完全缺失的模块

| 模块 | MemOS | Kairos | 差距 |
|:-----|:------|:-------|:-----|
| **Multi-Cube KB** | 可组合的记忆立方体，支持隔离+受控共享+动态组合 | 路径前缀隔离（kairos://_user/_project） | ▲ 架构级创新 |
| **三级技能进化** | L1 traces → L2 policies → L3 world model → crystallized Skills | 升华管道（raw→item→strategy→behavior） | ▲ Playbook 刚加，但无 L1-L3 进化 |
| **MemScheduler** | 异步摄取引擎，毫秒级延迟，生产级高并发 | 同步写入（加工区→验证→归档） | ▲ 高并发场景差距 |
| **图原生存储** | Neo4j 图谱，记忆间的关系是一等公民 | 关系索引表（邻接表，单跳查询） | ▲ 多跳深度差距 |
| **多模态记忆** | 文本+图像+工具轨迹一体化 | 纯文本 | ▲ |
| **Memory Viewer** | Web 可视化仪表板 | 无 | ▲ |

### 2.2 值得借鉴的设计

| 理念 | 说明 | 吸收方式 |
|:-----|:------|:---------|
| **Multi-Cube 思想** | 记忆立方体作为组合单元，每个 cube 可被多个 Agent 共享 | Kairos 路径空间已有隔离，可扩展 cube 概念 |
| **三级技能进化** | L1(痕迹)→L2(策略)→L3(世界模型)→Skills | 在 Playbook 系统之上增加进化层级 |
| **反馈驱动的检索** | NL 反馈 → 自动修正/补充/替换记忆 | Kairos 已有纠正检测，可吸收 NL 反馈 |
| **异步 MemScheduler** | 写入不阻塞检索 | Kairos 加工区已是异步，但缺正式调度器 |
| **Memory Viewer** | 可视化仪表板，不用 CLI 也能管理记忆 | 长期需求 |

---

## 三、Kairos 改造方案

### 需改造模块

| P | 模块 | 方向 |
|:-|:-----|:------|
| **P0** | **三级技能进化** | 在 Playbook 系统之上增加进化层级 |
| P2 | Multi-Cube 隔离 | 扩展路径空间 |
| P2 | Memory Viewer | Web 仪表板 |

### P0：三级技能进化（Skill Evolution）

**当前**：Kairos 的升华管道有 L0-L4 层级蒸馏（journal→session→daily→weekly→profile），新加的 Playbook 系统管理 strategy→behavior 产物。但缺少「技能」概念——一条可复用的过程知识如何从原始痕迹逐步进化到稳定技能。

**改造**：在升华管道 + Playbook 系统之上定义三级技能进化：

```
L1 Traces（痕迹层）
  原始对话片段的模式标记——不独立存储，由 L2 蒸馏消费
  │ 升华管道 L0→L1 阶段自动标记
  ▼
L2 Policies（策略层）
  可复用的操作策略——对应升华管道的 strategy 阶段输出
  存储为 Playbook candidate，confidence < 0.7 时保持 candidate 状态
  │ 经 Playbook 反馈循环提升 confidence
  ▼
L3 World Model（世界模型层）
  跨任务、跨 session 的稳定认知模式
  Playbook 中被连续多次 success 的模式→推广为 world model 规则
  存储为独立的 `world_model_rules` 表
  规则触发条件：同一操作模式在 ≥3 个不同 task_class 下 success ≥5 次
  │
Skills（结晶技能）
  经过严格验证的可交付技能库
  Playbook status=promoted + success_count ≥ 10 + 被 ≥2 个独立上下文引用
  自动注册到 Hermes skill 目录（或 MCP 工具）供跨会话调用
```

**与现有机制的关系**：
- L1 Traces → 升华管道 L0→L1 已有
- L2 Policies → Playbook candidate（4 轮分析刚新增）
- L3 World Model → 新增 `world_model_rules` 表
- Skills → Playbook promoted 状态 + Hermes skill 注册接口

**新增存储**：`world_model_rules` 表（rule_id, task_class, trigger_condition, action_template, preconditions, confidence, evidence_count, created_at）

**新增配置**：`KAIROS_SKILL_PROMOTION_MIN_SUCCESS`=10，`KAIROS_SKILL_PROMOTION_MIN_CONTEXTS`=2，`KAIROS_WORLD_MODEL_MIN_CLASSES`=3，`KAIROS_WORLD_MODEL_MIN_SUCCESS`=5

---

## 四、不纳入的内容

| 特性 | 不纳入理由 |
|:-----|:-----------|
| **Multi-Cube KB** | Kairos 路径空间（`kairos://_user/_project/_session`）已实现等价隔离，cube 概念可扩展但当前不急需 |
| **Neo4j 图存储** | Kairos 使用 PostgreSQL 递归 CTE + 关系索引表，开发运维成本更低。v1.1 才评估是否迁移到 Apache AGE |
| **Qdrant 向量引擎** | 未决定 vector 后端 |
| **多模态记忆** | 当前版本只做文本——多模态是远期需求 |
| **Memory Viewer** | P2，文档阶段不评估 UI 需求 |
| **MemScheduler 异步引擎** | Kairos 的加工区 + 后台维护引擎已实现「写入→异步蒸馏→验证→归档」 |
