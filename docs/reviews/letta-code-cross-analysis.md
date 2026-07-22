---
title: Letta Code (new) 对比分析与 Kairos 改造方案
aliases:
  - Letta Code Cross Analysis
tags:
  - kairos
  - analysis
  - comparison
  - design
created: 2026-07-22
status: merged-into-architecture
---

> **⚠️ 本文档为设计思考记录，所有内容已合并至 `architecture-v1.0.0.md`。**
> **开发请以 `architecture-v1.0.0.md` 为准，本文不保证与文档实时同步。**

# Letta Code 对比分析与 Kairos 改造方案

## 一、项目概要

### Letta Code v0.28.15（原 MemGPT 团队）

| 属性 | 值 |
|:----|:----|
| 定位 | **有状态 Agent 运行时**——像人一样的 Agent（记忆+身份+持续学习） |
| 技术栈 | TypeScript + Bun + MemFS + npm |
| 规模 | 2.9k stars, 2,870 commits, 237 releases, 日均发布 |
| 核心创新 | MemFS（git 版控上下文）、Memory Blocks（Agent 自编辑提示词）、Dreaming（休眠期自主学习） |
| 研究背景 | MemGPT (NeurIPS'24) + Sleep-time Compute (2025)，持续学习方向学术前沿 |

### 与旧版 Letta 的区别

旧版 Letta（v0.16.8）是 Python FastAPI 服务器，已归档。  
新版 **Letta Code** 是 TypeScript Agent 运行时——一个 CLI/桌面应用，不是 API 服务器。两者是不同的产品。

---

## 二、核心差异分析

### Kairos 已有覆盖

| Letta Code | Kairos | 状态 |
|:-----------|:-------|:-----|
| Memory Blocks（结构化 Agent 提示词） | SOUL.md + Playbook + 提示词优化器 | ✅ |
| Self-improvement | 自反思元记忆优化 + 提示词优化 | ✅ |
| Dreaming（休眠期计算） | 后台维护 Deep 模式 | ✅ |
| Skills（可安装技能） | Playbook 系统 + 三级技能进化 | ✅ |
| Subagents | 多 Agent 路径隔离 | ✅ |
| Message search | 5D 混合检索 | ✅ |

### Letta Code 独有的设计

| 特性 | 说明 | 差距 |
|:-----|:------|:------|
| **MemFS（Git 版控上下文）** | 所有 Agent 上下文（含 memory blocks）用 git 追踪，可同步到 GitHub。自带 diff/revert/历史 | **▲ 值得吸收** |

---

## 三、Kairos 改造方案

### P1：MemFS 风格上下文版本管理

**当前**：Kairos 通过 HMAC 审计链追踪记忆变更，但记忆内容本身不做版本管理——Update 操作覆盖旧值，只有审计日志记录了变更。

**改造**：在现有审计日志基础上，增加可选的上下文版本管理——

**设计**：
- 为 memories 表的每次 Update 操作保留快照——在 `memory_versions` 表中存储变更前的完整内容
- 支持按时间点查看特定记忆的历史版本（`GET /v1/memories/{id}/versions`）
- 支持回滚到指定版本（`POST /v1/memories/{id}/rollback?version=N`）
- 回滚操作用户审计日志，标记 `rollback`

**新增表 `memory_versions`**：

| 列名 | 类型 | 说明 |
|:-----|:-----|:------|
| id | BIGSERIAL PK | |
| memory_id | UUID FK | 关联记忆 |
| version | INTEGER | 版本号（递增） |
| content_snapshot | TEXT | 变更前内容快照 |
| change_type | TEXT | update / rollback |
| change_reason | TEXT | |
| created_at | TIMESTAMPTZ | |

**配置**：`KAIROS_MEMORY_VERSIONING_ENABLED`（默认 true），`KAIROS_MEMORY_VERSION_LIMIT`（默认 50，单条记忆最多保留的快照数）
