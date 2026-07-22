---
title: Memobase 对比分析与 Kairos 改造方案
aliases:
  - Memobase Cross Analysis
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

# Memobase 对比分析与 Kairos 改造方案

## 一、项目概要

### Memobase v0.0.40

| 属性 | 值 |
|:----|:----|
| 定位 | **用户画像记忆系统**——面向 AI Chatbot 的长期用户记忆 |
| 技术栈 | Python (FastAPI) + PostgreSQL + Redis + MCP |
| 规模 | 2.8k stars, 467 commits, Python/TS/Go 三 SDK |
| 核心范式 | **User Profile 优先**——不是 Agent 记忆，而是用户画像 + 事件时间线 |
| 设计哲学 | Buffer → Flush → Profile/Event 三步流水线 |

### Memobase 与之前所有项目的根本区别

之前 12 个项目都是 **Agent 记忆系统**（为 AI Agent 存储/检索记忆）。Memobase 是 **用户画像系统**（为 Chatbot 应用记忆用户是谁）。

这种范式差异意味着其核心设计围绕的是：
- **用户画像的结构化抽取**（姓名/职业/兴趣→可控的 profile schema）
- **非热路径批量处理**（buffer→flush，不在对话中实时处理）
- **事件时间线**（支持时间相关的用户行为回溯）

---

## 二、Kairos 已有覆盖

| Memobase | Kairos 对应 | 状态 |
|:---------|:------------|:-----|
| 用户画像存储 | `user_profiles` 表（preferences/traits） | ✅ data-model |
| 用户事件时间线 | 对话历史持久化 + 事件总线 | ✅ §5.2 |
| Buffer→Flush 异步处理 | 加工区（Processing Zone）+ 后台维护 | ✅ §5.10 |
| 非热路径批量提取 | 升华管道离线处理 | ✅ §5.2 |
| 用户隔离 | `kairos://_user/` 路径前缀 | ✅ §5.2 |
| MCP 集成 | MCP Bridge 12 工具 | ✅ §7.3 |
| Multi-SDK（Python/TS/Go） | Hermes Agent Tool + REST API + CLI | ○ |

### 唯一值得借鉴的设计

| 特性 | 说明 | 吸收计划 |
|:-----|:------|:---------|
| **用户画像 Schema 可配置** | 开发者可定义 profile 的 schema，指定提取哪些字段（如 name/age/interests），Memobase 按 schema 抽取 | P2。Kairos 的 user_profiles 表已有基础字段，可扩展 schema 配置 |

---

## 三、不纳入的内容

| 特性 | 不纳入理由 |
|:-----|:-----------|
| Buffer→Flush 模型 | Kairos 加工区 + 后台维护引擎已实现等价的异步批处理 |
| 非热路径写入 | 与加工区设计一致——写入加工区，异步蒸馏 |
| Profile 优先范式 | Kairos 定位是通用记忆系统（兼顾 Agent 记忆和用户记忆），不是 Chatbot 专用 |
| LOCOMO SOTA | 评测方向和 Kairos 不同 |
