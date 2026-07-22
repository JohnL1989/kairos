---
title: Supermemory 对比分析与 Kairos 改造方案
aliases:
  - Supermemory Cross Analysis
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

# Supermemory 对比分析与 Kairos 改造方案

## 一、项目概要

### Supermemory

| 属性 | 值 |
|:----|:----|
| 定位 | AI 的记忆与上下文引擎——Memory ≠ RAG |
| 技术栈 | TypeScript + Python + Cloudflare Workers + Drizzle ORM + Postgres |
| 规模 | **28.5k stars**, 1,785 commits, #1 on LongMemEval/LoCoMo/ConvoMem |
| 核心创新 | **Memory vs RAG 分离** + **自动临时事实过期** + **MemoryBench** |
| Benchmark | 95% R@15, 99.4% 上下文缩减, ~50ms 用户画像 |

---

## 二、Kairos 已有覆盖

| Supermemory | Kairos | 状态 |
|:-----------|:-------|:-----|
| Memory Engine（事实提取+更新+矛盾+过期） | 升华管道 + 知识演化 + fact_freshness | ✅ |
| User Profiles（静态+动态） | user_profiles 表 | ✅ |
| Hybrid Search（RAG + Memory） | 5D 混合排序 | ✅ |
| Multi-modal Extractors | 分块引擎（文本） | ✅ |
| Auto-forgetting | 遗忘调度器 + fact_freshness | ✅ |
| Connectors（Google Drive/Gmail/Notion/GitHub） | 外部数据摄取（规划中） | ✅ 已计划 |
| Framework Integrations（Vercel AI SDK/LangChain） | MCP Bridge + Memory Provider | ✅ |

### Supermemory 独有的设计

| 特性 | 说明 | 差距 |
|:-----|:------|:------|
| **临时事实智能过期** | 自动检测事实中的时间指示（"明天考试""下周搬家"），到期自动清理。非固定 TTL | **▲ 值得吸收** |
| **Memory vs RAG 显式分离** | 用户记忆和知识库检索用不同路径优化，不混在一体 | 理念差异，非架构项 |

---

## 三、Kairos 改造方案

### P0：临时事实智能过期

**当前**：Kairos 的 fact_freshness 使用固定 TTL——写入时指定 `ttl_days`，到期标记 expired。无法自动检测"临时性"事实。

**改造**：在后台维护 Deep 模式的事实新鲜度扫描阶段增加临时事实检测——

**检测方法**：
- 对新增记忆扫描内容中的时间指示模式（正则 + LLM 辅助）
- 时间模式：明确的未来时间点（"下周""明天""下个月""June 15"）、临时状态（"在找""正在申请""临时"）
- 对匹配临时模式的事实，自动设置合理的 `valid_until`（基于检测到的日期 + 合理缓冲期）
- 未匹配临时模式的事实保持 `valid_until = NULL`（永久有效，等待其他失效机制）

**检测示例**：

| 内容 | 检测结果 | valid_until |
|:-----|:---------|:------------|
| "我明天有个考试" | 临时（detected: 明天） | 考试次日后 |
| "正在申请 Google 的岗位" | 临时（detected: 正在申请） | 当前日期 + 90 天 |
| "喜欢喝黑咖啡" | 永久（no pattern） | NULL |
| "下周要搬到 SF" | 临时（detected: 下周） | 预计搬家后 + 30 天 |

**配置参数**：`KAIROS_TEMPORAL_EXPIRY_ENABLED`（默认 true），`KAIROS_TEMPORAL_EXTRA_BUFFER_DAYS`（默认 7），`KAIROS_TEMPORAL_APPLY_THRESHOLD`（默认 0.7，检测置信度阈值）
