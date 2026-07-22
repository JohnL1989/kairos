---
title: LangMem 对比分析与 Kairos 改造方案
aliases:
  - LangMem Cross Analysis
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

# LangMem 对比分析与 Kairos 改造方案

## 一、项目概要

### LangMem（LangChain）

| 属性 | 值 |
|:----|:----|
| 定位 | LangGraph Agent 的记忆管理库——提取、优化、持久化 |
| 技术栈 | Python + LangGraph BaseStore + Trustcall |
| 规模 | 1.6k stars, 139 commits, LangChain 官方 |
| 核心创新 | **Prompt Optimization**（3 策略梯度/元提示/记忆）+ Multi-Prompt Credit Assignment |

---

## 二、核心差异分析

### 2.1 Kairos 已覆盖的能力

| LangMem | Kairos 对应 | 状态 |
|:--------|:------------|:-----|
| create_manage_memory_tool | MCP Bridge 12 工具 (§7.3) | ✅ |
| create_search_memory_tool | 5D 混合检索 (§7.3) | ✅ |
| create_memory_manager | 升华管道 L0-L4 (§5.2) | ✅ |
| create_thread_extractor | 对话历史 + L1→L2 蒸馏 (§5.2) | ✅ |
| ReflectionExecutor | §10.15 自反思元记忆优化 | ✅ |
| LangGraph BaseStore | PostgreSQL/SQLite 双后端 | ✅ |

### 2.2 LangMem 独有的设计

| 特性 | LangMem | Kairos | 差距 |
|:-----|:--------|:-------|:-----|
| **Prompt Optimization** | 3 策略（gradient/metaprompt/prompt_memory）优化系统提示词 | 无 | **▲ 值得吸收** |
| **Multi-Prompt Credit Assignment** | 识别多个提示词中哪条导致性能下降，仅优化该条 | 无 | **▲ 值得吸收** |

---

## 三、Kairos 改造方案

### P0：Prompt Optimization（提示词优化）

**当前**：Kairos 的系统提示词（Hermes SOUL.md、MCP tools 描述、playbook 上下文注入 prompt）都是静态的——不因使用反馈而优化。

**改造**：新增提示词优化器——随后台维护 Deep 模式执行，基于对话轨迹和反馈自动优化系统提示词。

**三种策略**：

1. **Gradient（梯度优化）**：分离"评估"与"更新"两个关注点——先用 LLM 反思当前提示词的不足，再基于反思生成改进版本。每轮 2 次 LLM 调用（思考+更新），可配置轮次 1-5
2. **Meta-Prompt（元提示优化）**：直接用元提示分析轨迹并生成改进——更快（单次调用/轮），适合幅度较小的改进
3. **Prompt Memory（提示记忆）**：从历史成功模式中提取有效策略，应用到当前提示词——最快（1 次 LLM 调用）

**集成位置**：提示词优化器作为 §10.15 自反思元记忆优化的同级组件——元记忆优化关注"怎么用记忆"，提示词优化关注"怎么组织提示词"，两者互补。

**消费方式**：优化后的提示词通过 `POST /v1/prompts/optimize` 接口输出。不同策略的优化结果由宪法主权面的外部校准端口验证——校准信号可回滚至上一版本。

**配置参数**：
- `KAIROS_PROMPT_OPT_STRATEGY`（默认 gradient）：gradient / metaprompt / prompt_memory
- `KAIROS_PROMPT_OPT_REFLECTION_STEPS`（默认 3，range 1-5）
- `KAIROS_PROMPT_OPT_MIN_STEPS`（默认 1）
- `KAIROS_PROMPT_OPT_AUTO_ROLLBACK`（默认 true）：校准反馈连续 2 次 negative 自动回滚

**多提示词信用分配**（Multi-Prompt Credit Assignment）：当系统使用多条提示词（如 SOUL.md + skill + playbook context），优化器先通过 Agent 推理分析判定哪条提示词导致性能下降，仅对问题提示词执行优化，其余保持原样。
