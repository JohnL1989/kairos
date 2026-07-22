---
title: memU 对比分析与 Kairos 改造方案
aliases:
  - memU Cross Analysis
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

# memU 对比分析与 Kairos 改造方案

## 一、项目概要

### memU v1.5.1

| 属性 | 值 |
|:----|:----|
| 定位 | Personal memory across agents——以文件为媒介的个人记忆系统 |
| 技术栈 | Python (Pydantic) + SQLite/PostgreSQL + 纯向量检索 |
| 规模 | 14k stars, 374 commits, 500 行核心代码 |
| 设计哲学 | 极简——只用 embedding，不用 LLM |
| 核心创新 | Segment 逐行差分索引、三层递进检索、Host adapter 多代理桥接 |

### memU 回答的根本问题

> **如何用最小的模型调用成本（仅 embedding），实现跨 Agent 的持久化记忆？**

它的答案是：Agent 自己把值得记的内容写成 Markdown，memU 只管分段→嵌入→排序。

---

## 二、核心差异分析

### 2.1 memU 有而 Kairos 无的独特设计

| 特性 | memU | Kairos | 差距 |
|:-----|:------|:-------|:-----|
| **Segment 差分索引** | 按行 diff：只 embedding 新增行，删除行删向量，不变行保留 | 全量重嵌入 | **▲ 值得吸收** |
| **三层递进检索** | segments→files→resources，一次 embedding 调用出三层 | 多路径融合更复杂 | ○ 各有优势 |
| **Host adapter** | 7 种 Agent 的标准化桥接（Codex/Claude/Cursor/OpenClaw/Hermes/WorkBuddy/通用） | 仅 Hermes MCP Bridge | ▲ 值得借鉴适配层设计 |
| **SKILL.md 驱动安装** | Agent 读 SKILL.md → 自动识别宿主→打印安装指南→引导执行 | 手动安装 | ○ 理念不同 |
| **纯 embedding** | 整个系统只调用 embedding API | 5D 混合排序+LLM 蒸馏 | 定位不同 |

### 2.2 memU 的极简设计理念

| 理念 | 说明 |
|:-----|:------|
| **Memorization ≠ LLM** | 记忆系统的核心是存储和检索，不需要 LLM 参与。只用 embedding 就够了——LLM 是消费记忆的，不是管理记忆的 |
| **Agent 自己是记忆的编辑者** | memU 不做蒸馏/总结/消歧——Agent 自己在对话中决定什么值得记成 Markdown，memU 只管存和查 |
| **Cost matters** | 写时只对新行做 embedding，检索时只做一次 embedding——没有 LLM 调用，没有多轮路由，降低成本至极限 |

---

## 三、Kairos 改造方案

### 需改造模块

| P | 模块 | 方向 |
|:-|:-----|:------|
| **P0** | **Segment 差分索引** | 写入时只对新/删内容做 embedding，不变内容保留向量 |
| P2 | Host adapter 扩展 | 增加对其他 Agent（Codex/Claude Code/Cursor/WorkBuddy）的适配器 |

### P0：Segment 差分索引

**当前**：Kairos 的记忆写入是整条 embedding——即使只修改了一行内容，也会重新计算整条记忆的向量。

**改造**：在分块引擎（Chunking Engine）的基础上，增加段级别差分同步：

```
写入请求
  │
  ├─ 新记忆 → 正常分块 + 全量 embedding
  │
  └─ 更新已有记忆 → 分块引擎执行差分：
       ├─ 读取现有分块的 text_hash 列表
       ├─ 重新分块：新文本 → 新分块列表
       ├─ diff：新有旧无 → embedding（仅新行）
       ├─      旧有新无 → 删除向量
       └─      新旧都有 → 保留向量（text_hash 匹配）
```

**约束**：
- 差分仅在 Update 操作（PATCH /v1/memories/{id}）时触发，Create 操作始终全量
- 差分通过对比分块的 `text_hash` 实现——每个分块存储 `SHA256(content)` 作为 diff 指纹
- 分块引擎新增 `memory_chunks.text_hash` 列
- 差分不绕过差异检验——即使只变更一行，仍触发 §10.7 差异检验流程
- 配置参数：`KAIROS_CHUNK_DIFF_ENABLED`（默认 true），`KAIROS_CHUNK_DIFF_MIN_SAVINGS`（默认 0.3，节省 <30% 时回退全量）

---

## 四、不纳入的内容

| 特性 | 不纳入理由 |
|:-----|:-----------|
| **纯 embedding** | Kairos 的 5D 混合排序需要 BM25/信任/热度等多维信号，纯 embedding 不符合设计 |
| **Agent 自编辑记忆** | Kairos 的设计原则是 P6 维度保护 + 双副本隔离——记忆写入需要经过校准和验证，不能让 Agent 自由写入 |
| **Host adapter** | P2，当前仅支持 Hermes。待 Kairos 成熟后可扩展 |
| **SKILL.md 安装** | 理念差异——Kairos 是后端服务，不是 Agent 插件 |
