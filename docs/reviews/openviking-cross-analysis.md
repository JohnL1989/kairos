---
title: OpenViking 对比分析与 Kairos 改造方案
aliases:
  - OpenViking Cross Analysis
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

# OpenViking 对比分析与 Kairos 改造方案

## 一、项目概要

### OpenViking v0.4.10

| 属性 | 值 |
|:----|:----|
| 定位 | AI Agent 的上下文数据库 |
| 技术栈 | Python + Rust CLI + TS Plugin + RAGFS |
| 规模 | **27k stars**, 1,768 commits, 字节跳动 |
| 核心创新 | RAGFS 文件系统、目录递归检索、可视化检索轨迹 |

### 吸收内容

| 设计 | 架构位置 |
|:-----|:---------|
| 递归路径检索模式（先定位目录→范围内检索→递归钻取→聚合） | §7.3 检索部分 |
| 可视化检索轨迹（结构化 trace + 可追溯路径） | §7.3 Recall Funnel 扩展 |
