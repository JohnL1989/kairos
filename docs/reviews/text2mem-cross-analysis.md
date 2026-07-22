---
title: text2mem 对比分析与 Kairos 改造方案
aliases:
  - Text2Mem Cross Analysis
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

# text2mem 对比分析与 Kairos 改造方案

## 一、回答的根本问题

> **记忆操作如何从"自然语言模糊意图"转化为"可执行、可审计、可移植的标准化指令"？**

text2mem 不是记忆存储系统，而是一个 **统一记忆操作语言（Unified Memory Operation Language）**。它解决的不是"怎么存/怎么查"，而是"存储/检索/治理这些操作应该长什么样才规范"。

---

## 二、核心价值

### text2mem 的 12 个标准操作（Operation Schema）

| 阶段 | 操作 | 说明 |
|:-----|:-----|:------|
| **ENC**（编码） | `Encode` | 存储带嵌入的新记忆 |
| **RET**（检索） | `Retrieve` | 语义/关键词混合搜索 |
| | `Summarize` | 生成选定记忆摘要 |
| **STR**（存储治理） | `Label` | 添加标签/分面 |
| | `Update` | 修改记忆字段 |
| | `Promote` | 提升权重/设提醒 |
| | `Demote` | 降低权重/归档 |
| | `Merge` | 合并多条记忆 |
| | `Split` | 拆分记忆 |
| | `Lock` | 保护记忆不被修改 |
| | `Expire` | 设置过期时间 |
| | `Delete` | 软/硬删除 |

### IR 结构

```json
{"stage": "ENC|RET|STR", "op": "...", "target": {...}, "args": {...}, "meta": {...}}
```

---

## 三、四维对比分析

### 3.1 架构设计对比

| 维度 | text2mem | Kairos | 优势 |
|:-----|:--------|:-------|:-----|
| **定位** | 操作协议/语言层 | 完整记忆系统 | 不同层面，不直接可比 |
| **核心抽象** | `stage/op/target/args/meta` 五元组 | REST API + Agent Tool | **▲ text2mem 更标准化** |
| **操作治理** | 12 canonical ops + safety invariants | 隐式操作（通过 API/工具） | **▲ text2mem 显式清单** |
| **校验层** | JSON Schema + Pydantic v2 双校验 | 摄取验证门禁 + 安全红线 | **▲ text2mem 分层更清晰** |
| **执行管道** | Validator → Parser → Adapter | 接入层→WM→存储层 | Kairos 更完整 |

### 3.2 核心功能对比

| 功能 | text2mem | Kairos | 差距 |
|:-----|:--------|:-------|:-----|
| **标准操作集** | 12 个显式规范操作 | 隐式 API 端点 + 工具 | **▲ text2mem 可移植性更好** |
| **Clarify（消歧）** | 预澄清步骤，补足欠约束信息 | 无 | **▲ 值得吸收** |
| **Safety Invariants** | Lock/Expire 语义 + 破坏性操作确认 | 安全红线（S-01~S-17） | Kairos 更全面 |
| **Dual Validation** | JSON Schema + Pydantic v2 | 接入层校验 | **▲ text2mem 设计模式更清晰** |
| **Adapter 抽象** | SQLite（ref）+ Postgres（TODO） | PostgreSQL + SQLite | ○ 类似 |
| **Benchmark** | 2 层（NL→IR + IR→state） | 性能基准计划 | **▲ text2mem 语义测试更好** |

### 3.3 值得借鉴的设计理念

| 理念 | 说明 |
|:-----|:------|
| **显式操作清单** | 12 个 canonical ops 让"系统能做什么"文档化，Kairos 应编写类似的 Operation Catalog |
| **Clarify 步骤** | 在执行前解析"未说清楚"的意图，减少误解执行 |
| **Validator → Parser → Adapter 流水线** | 将"校验"和"执行"分离为独立阶段 |
| **Two-layer benchmark** | 计划层（NL→正确IR）与执行层（IR→正确状态）分开评测 |

---

## 四、Kairos 吸收方案

### 需要改造的模块

| P | 模块 | 方向 |
|:-|:-----|:------|
| **P0** | **Kairos Operation Catalog** | 编写显式操作清单，统一文档中散落的 API/工具定义 |
| **P1** | **Clarify 消歧步骤** | 在 MCP Bridge 工具调用前增加意图消歧层 |
| **P2** | **Two-stage Benchmark** | 在现有基准计划中增加 NL→正确API调用 的评测层 |

### P0：Kairos Operation Catalog

**当前**：Kairos 的操作分布在架构文档各处——§7 定义接入方式、api-spec.md 定义 REST 端点、feature-list.md 定义 80 项功能。没有一份集中的"系统能做什么"的显式操作清单。

**改造**：新增 `specification/operation-catalog.md`，按三阶段（ENC/RET/STR）组织所有操作：

| 阶段 | 操作 | 映射 | 说明 |
|:-----|:-----|:------|:------|
| **ENC** | 按路径写入 | POST /v1/memories | |
| | 批量写入 | POST /v1/memories/batch | |
| | 三区写入 | POST /v1/memories + hall=processing | |
| **RET** | 语义检索 | POST /v1/memories/search | 5D 混合排序 |
| | 路径检索 | GET /v1/path | |
| | 实体图谱检索 | POST /v1/graph/search | |
| | 时间序检索 | GET /v1/memories?sort=created_at | |
| | 会话检索 | GET /v1/sessions | |
| | Playbook 检索 | GET /v1/playbooks/search | |
| **STR** | 更新 | PATCH /v1/memories/{id} | 版本插入 |
| | 删除（软/硬） | DELETE /v1/memories/{id} | 按契约分级 |
| | 定向遗忘 | POST /v1/memories/{id}/suppress | |
| | 归档 | POST /v1/memories/{id}/archive | Active→Archived |
| | 标签标注 | POST /v1/memories/{id}/tags | |
| | 推进 | POST /v1/halls/promote | 加工区→验证区→正式库 |
| | 退回 | POST /v1/halls/demote | 验证区→加工区 |
| | 锁定 | POST /v1/memories/{id}/lock | 修改保护 |
| | 过期 | POST /v1/memories/{id}/expire | TTL 设定 |
| | 合并 | POST /v1/memories/merge | |
| | 反馈 | POST /v1/playbooks/{id}/feedback | |

### P1：Clarify 消歧步骤

在 MCP Bridge 的复杂操作前增加可选的意图澄清层——当 IR 的 target 或 args 信息不足时（如缺路径、缺契约、缺 VAD），Clarify 步骤可反问补全。

**实现**：在 MCP Bridge 中增加 `kairos_clarify` 工具，以及 Hermes Memory Provider 的 `on_pre_store` hook。输入为欠约束的 memory write 请求，输出为补全后的完整请求。

### P2：Two-stage Benchmark

在现有 benchmark-plan.md 的纯性能指标之外，增加语义评测层：
- **操作正确率**：NL 意图 → 正确 API 调用的成功率
- **状态正确率**：操作执行后存储状态是否符合预期
- **安全合规率**：destructive 操作的安全门禁触发率

---

## 五、不纳入的内容

| 特性 | 不纳入理由 |
|:-----|:-----------|
| text2mem 的 JSON IR 格式 | Kairos 已有 REST API schema，无需第二套 IR |
| Pydantic 双校验 | Kairos 使用 Litestar + Pydantic，已有请求校验 |
| Adapter 抽象 | Kairos 的多路径融合 + 存储后端抽象已覆盖 |
