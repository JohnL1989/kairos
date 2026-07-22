---
title: Letta 对比分析与 Kairos 改造方案
aliases:
  - Letta Cross Analysis
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

# Letta 对比分析与 Kairos 改造方案

## 一、项目概要

### Letta v0.16.8（原 MemGPT）

| 属性 | 值 |
|:----|:----|
| 定位 | 有状态 Agent 平台——AI 具高级记忆+自我进化能力 |
| 技术栈 | Python + PostgreSQL + Alembic + FastAPI + Docker |
| 规模 | **23.9k stars**, 7,467 commits, 177 releases, 157 contributors |
| 状态 | ⚠️ 此仓库为旧版 Letta Server。**长期开发已迁移至 `letta-ai/letta-code`** |

---

## 二、Kairos 已有覆盖

| Letta 核心概念 | Kairos 对应 | 状态 |
|:--------------|:------------|:-----|
| Core Memory（Persona + Human） | user_profiles + 路径空间 | ✅ |
| Archival Memory（混合检索） | 5D 混合排序 + MCP 工具 | ✅ |
| Recall Memory（对话历史） | 对话历史持久化 | ✅ |
| 工具/函数系统 | MCP Bridge 12 工具 | ✅ |
| Subagents | 多 Agent 路径隔离 + Memory Provider | ✅ |
| Skills | Playbook 系统 + 三级技能进化 | ✅ |
| 上下文窗口管理 | 升华管道 + 遗忘调度器 | ✅ |
| MCP 集成 | MCP Bridge + Memory Provider hooks | ✅ |

### Letta 独有的设计（已被旧版标记，不再活跃开发）

| 特性 | 说明 | 判断 |
|:-----|:------|:-----|
| **Persona + Human 核心记忆块** | Agent 身份和用户信息的结构化内存块，支持版本编辑 | Kairos `user_profiles` 表 + 路径空间已覆盖。不额外吸收 |
| **上下文压力告警** | 监控 token 用量，超阈值时触发 summarizer 告警 | 属于 Agent 运行时层。Kairos 的升华管道 + 加工区由后台维护引擎调度，不依赖实时 context window 压力 |
| **Tool execution sandbox** | 工具执行的沙箱隔离 | 属于 Agent 运行时安全，非内存系统设计 |

---

## 三、结论

**Letta（旧版仓库）不产生需要吸收的新设计。**

原因：
1. **此仓库已标记为 legacy**——"Active development has moved to the Letta Agent repo"
2. Letta 的核心设计（Core Memory / Archival Memory / Recall Memory / Summarizer）在 Kairos 此前 15 个项目的吸收中已全部覆盖
3. Letta 唯一的独特模式——"Context Window Pressure → Summarization"——属于 Agent 运行时层的内存管理，Kairos 将其委托给 Hermes Agent 运行时，由升华管道 + 加工区处理等价功能

**Kairos 最终累计：43 → 96 项能力**（16 个项目中 15 个有吸收贡献）
