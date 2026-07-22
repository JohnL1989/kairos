---
title: MetaMem 对比分析与 Kairos 改造方案
aliases:
  - MetaMem Cross Analysis
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

# MetaMem 对比分析与 Kairos 改造方案

## 一、项目概要

### MetaMem（ACL 2026 Findings）

| 属性 | 值 |
|:----|:----|
| 定位 | 通过自反思符号优化进化元记忆的知识利用框架 |
| 技术栈 | Python + LightMem + Qdrant + SGLang |
| 规模 | ACL 2026 Findings 论文，OpenBMB 出品 |
| 核心创新 | Self-Reflective Symbolic Optimization——用自反思循环 + 符号操作（add/update/delete）迭代优化元记忆原则 |

### MetaMem 回答的根本问题

> **Agent 如何从每一次检索→回答的成败中学习「更好地使用记忆」的策略？**

它不是问「怎么存/怎么查」（存储/检索问题），而是问：「拿到检索结果后，怎么读、怎么用、怎么拼？」（利用策略问题）。

### 吸收内容：§10.15 自反思元记忆优化

已在架构文档 §10.15 完整定义——轨迹分析 → 跨轨迹对比 → 原则提炼(add/update/delete) → 消费流程。
