---
title: TencentDB Agent Memory 对比分析与 Kairos 改造方案
aliases:
  - TencentDB Agent Memory Cross Analysis
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

# TencentDB Agent Memory 对比分析与 Kairos 改造方案

## 一、项目概要

### TencentDB Agent Memory

| 属性 | 值 |
|:----|:----|
| 定位 | 本地长期记忆——4 层递进流水线，零外部 API 依赖 |
| 技术栈 | TypeScript + SQLite + sqlite-vec + Mermaid |
| 规模 | 103 commits, 腾讯云出品, OpenClaw/Hermes 插件 |
| 核心范式 | **L0-L3 语义金字塔 + Symbolic Memory（Mermaid Canvas）** |
| 核心数据 | 接入 OpenClaw 后 token 节省 **61.38%**，PersonaMem 准确率从 **48%→76%** |

### 核心架构：L0-L3 语义金字塔

| 层级 | 存储 | 内容 | 类比 Kairos |
|:-----|:-----|:------|:------------|
| L3 Persona | Markdown 文件 | 用户画像、长期偏好 | user_profiles ✅ |
| L2 Scenario | Markdown 文件 | 任务场景、上下文 | 路径空间 ✅ |
| L1 Atom | 结构化 DB | 原子事实、关键信息 | memories 表 ✅ |
| L0 Conversation | 原始文本 | 完整对话 | 对话历史 ✅ |

---

## 二、Kairos 已有覆盖

| TencentDB | Kairos | 状态 |
|:----------|:-------|:-----|
| L0-L3 语义分层 | 三级架构梯度 + 升华管道 L0-L4 | ✅ |
| 多层级检索 drill-down | 路径空间树状浏览 + 递归路径检索 | ✅ |
| BM25 + Vector + RRF 混合 | 5D 混合排序 | ✅ |
| Hermes 集成 | MCP Bridge + Memory Provider | ✅ |
| OpenClaw 集成 | 跨平台身份映射（规划中） | ✅ 已计划 |
| 白盒可调试（Markdown 文件） | operation-catalog.md + Recall Funnel | ✅ |

### 独有设计

| 特性 | 说明 | 差距 |
|:-----|:------|:------|
| **Symbolic Memory（Mermaid Canvas）** | 将 LLM 的冗长中间输出（搜索\结果、代码块、错误追踪）压缩为结构化的 Mermaid 节点图——在保留语义的同时节省 token | **▲ 值得吸收** |

---

## 三、Kairos 改造方案

### P1：Symbolic Compression（符号化压缩）

**当前**：Kairos 的升华管道通过 L0→L4 蒸馏压缩记忆，但对 LLM 中间输出（搜索结果、代码块、错误日志）没有专门的压缩机制——这些内容以原文形式存储，token 占用大。

**改造**：在升华管道的 L1→L2 阶段增加可选的符号化压缩步骤——

**方法**：
- 对 LLM 中间输出（搜索结果集、代码块、错误追踪）检测结构特征
- 对可结构化表达的内容（搜索结果、代码片段、错误链）生成结构化摘要而非原文存储
- 结构化摘要保留充分的证据信息（结果数量、代码行数、错误类型），但不保留全文
- 原始内容写入 `refs/` 路径（`kairos://_session/_refs/`），通过 `result_ref` 引用关联——保持 drill-down 能力

**符号化类型**：

| 类型 | 原文形式 | 符号化形式 | 压缩比 |
|:-----|:---------|:-----------|:-------|
| 搜索结果集 | 10 条搜索结果原文 | 结构化摘要（数量+最佳结果+关键实体） | ~80% |
| 代码块 | 完整代码 | 结构化摘要（语言/功能/关键函数/行数） | ~70% |
| 错误追踪 | 完整 traceback | 结构化摘要（错误类型/关键栈帧/根因） | ~90% |
| 工具调用结果 | 完整 JSON 输出 | 结构化摘要（操作类型/状态/关键字段） | ~60% |

**约束**：
- 符号化压缩为可选项，通过 `KAIROS_SYMBOLIC_COMPRESSION`（默认 true）启控
- 原始内容始终保留在 refs 路径中，符号化内容仅作为检索层的替代呈现
- 符号化不绕过差异检验——仅改变存储格式，不影响校验逻辑
