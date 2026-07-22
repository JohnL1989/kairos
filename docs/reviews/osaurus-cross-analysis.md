---
title: Osaurus 对比分析与 Kairos 改造方案
aliases:
  - Osaurus Cross Analysis
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

# Osaurus 对比分析与 Kairos 改造方案

## 一、项目概要

### Osaurus v0.22.4

| 属性 | 值 |
|:----|:----|
| 定位 | macOS 原生 AI 赋能工具（Agent Harness）——不是记忆系统 |
| 技术栈 | Swift + MLX + SQLite + Apple Containerization + MCP |
| 规模 | 7.2k stars, 3,172 commits, 434 releases, 腾讯云/Apple 生态 |
| 核心范式 | 身份+记忆+工具+沙箱 全栈 macOS 原生 |
| 设计哲学 | **推理是可替换的，Harness 是不可替换的** |

### 与 Kairos 的本质差异

Osaurus 是一个**完整的 Agent 运行时**（macOS 原生应用），记忆只是其众多组件之一。Kairos 是一个**记忆系统架构**。两者不在同一抽象层。

---

## 二、Kairos 已有覆盖

| Osaurus 记忆层 | Kairos 对应 | 状态 |
|:--------------|:------------|:-----|
| 三层记忆（身份+事实+会话） | user_profiles + memories + 对话历史 | ✅ |
| Salience 打分 | 5D 混合排序 + RL 优化器 | ✅ |
| 后台合并/衰减/淘汰 | 遗忘调度器 + 后台维护 | ✅ |
| ~800 tokens/turn 注入 | 加工区 + 优选调度 | ✅ |
| MCP 集成 | MCP Bridge 12 工具 | ✅ |
| 沙箱隔离 | WM 沙箱验证环 | ✅ |

### 独有的设计（与 Kairos 无关）

| 特性 | 说明 | 判断 |
|:-----|:------|:-----|
| **隐私过滤器** | 发送到云端前用 on-device 分类器检测 PII，fail-closed | 属于 Agent 运行时安全层，非记忆系统设计 |
| **加密身份体系** | secp256k1 地址 + X25519 端到端加密 | 属于 Agent 运行时安全，非记忆系统设计 |
| **沙箱 VM** | Apple Containerization 隔离 Linux VM | 属于 Agent 执行环境 |

---

## 三、结论

**不产生需要吸收的新设计。**

Osaurus 的独特价值在于它作为 macOS Agent 运行时的整体设计（加密身份、隐私过滤器、沙箱 VM、MCP 桥接）——这些是 Agent 运行时的工程创新，不是记忆系统的设计创新。

Kairos 作为记忆系统架构，其对应的抽象层（身份管理、安全红线、沙箱验证环、MCP 集成）已在 97 项能力中覆盖。Osaurus 在记忆层面的设计（三层记忆+salience+后台合并）没有超出 Kairos 此前 18 个项目的吸收范围。

**Kairos 最终累计：43 → 97 项能力**（18 个项目中 16 个有吸收贡献）
