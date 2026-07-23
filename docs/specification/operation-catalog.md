---
title: Kairos 操作目录
aliases:
  - 操作目录
  - Operation Catalog
tags:
  - kairos
  - design
  - api
created: 2026-07-22
status: draft
---

# Kairos 操作目录

> **定位**：将架构文档各处的 API 端点、Agent Tool、MCP Bridge 工具、CLI 命令汇聚为统一的显式操作清单。按三阶段（编码/检索/存储治理）组织，每操作标注安全红线、契约约束和 P6 合规状态。
>
> **与 api-spec.md 的关系**：操作目录是"系统能做什么"的外部视角——按意图而非按协议组织。api-spec.md 是"怎么调用"的协议层细节。两份文档互补不冲突。

---

## 一、编码阶段（ENC）

记忆的创建和摄入。

| 操作 | 映射端点 | 工具 | 安全红线 | 契约支持 | P6 合规 |
|:-----|:---------|:-----|:---------|:---------|:--------|
| 按路径写入 | POST /v1/memories | memories_write | S-03（长度）/S-09（注入）/S-15（来源） | permanent/ondemand/environmental/temporary | 条件激活（P6 受控例外） |
| 批量写入 | POST /v1/memories/batch | — | S-03/S-09 | 逐条独立 | ✅ |
| 三区写入 | POST /v1/memories + hall | — | S-03/S-09/S-17（结构反例） | 默认 ondemand | ✅ |
| 实体自动提取 | 写入时自动触发 | kairos_extract_entities | S-15 | — | ✅ |
| 冲突检测写入 | 写入时自动触发 | — | S-14（自指禁令） | — | ⚠️ 压缩~33% |
| 会话消息同步 | POST /v1/sessions/{id}/messages | — | S-15 | — | ✅ |
| 校准信号注入 | POST /v1/calibrate | kairos_calibrate | S-11（唯一入口） | — | ✅ |

## 二、检索阶段（RET）

记忆的查询和召回。

| 操作 | 映射端点 | 工具 | 安全红线 | 说明 |
|:-----|:---------|:-----|:---------|:-----|
| 语义检索 | POST /v1/memories/search | memories_search | S-02（限流） | 5D 混合排序（语义+BM25+时序+信任+热度） |
| 文本检索 | GET /v1/memories?q={query} | — | S-02 | 关键词全文检索（对应 requirements-baseline R-02） |
| 路径检索 | GET /v1/path | kairos_tree | S-02 | 确定性前缀匹配 |
| 路径空间浏览 | GET /v1/path/tree | kairos_tree | S-02 | 树状浏览 |
| 实体图谱检索 | POST /v1/graph/search | graph_search | S-02 | 递归 CTE 多跳 |
| 时间序检索 | GET /v1/memories?sort=created_at | — | S-02 | 纯时间轴，与热度解耦 |
| 分块检索 | 写入自动分块，检索时关联 | — | — | 200-600 字重叠窗口 |
| 会话列表 | GET /v1/sessions | sessions_list | S-02 | |
| 会话消息 | GET /v1/sessions/{id}/messages | — | S-02 | 游标分页 |
| 知识演化链 | GET /v1/evolution/{id} | — | — | replaces/enriches/confirms/challenges |
| 聚合健康报告 | GET /v1/health/detail | — | — | 按 type/state 聚合 + flags |
| 检索 Explain | GET /v1/search/explain | — | — | 附带 Recall Funnel trace |
| Playbook 搜索 | GET /v1/playbooks/search | — | — | FTS + 语义混合 |
| 热度最高记忆 | GET /v1/memories/heat-top | kairos_get_hot_memories | S-02 | |
| 记忆统计 | GET /v1/memories/stats | kairos_get_stats | — | 按 type/state 聚合 |

## 三、存储治理阶段（STR）

记忆的更新、管理、运维。

| 操作 | 映射端点 | 工具 | 安全红线 | 说明 |
|:-----|:---------|:-----|:---------|:-----|
| 记忆更新 | PATCH /v1/memories/{id} | — | S-15 | 版本插入，修改历史可审计 |
| 软删除 | DELETE /v1/memories/{id} | kairos_delete_memory | S-16（定向遗忘留痕）/S-17（结构反例豁免） | 依契约分级：permanent 拒绝/常驻按需软删/临时硬删 |
| 定向遗忘 | POST /v1/memories/{id}/suppress | — | S-16 | 抑制检索，保留数据 |
| 标记过期 | POST /v1/memories/{id}/expire | — | — | 设 TTL，到期自动归档（已定义于 api-spec §1.3） |
| 锁定 | POST /v1/memories/{id}/lock | — | — | 保护不被修改 |
| 合并 | POST /v1/memories/merge | kairos_merge | S-14 | 语义合并，保留见证锚定 |
| 路径抑制 | POST /v1/path/suppress | — | S-16/S-17 | 路径级检索抑制 |
| 区推进 | POST /v1/halls/promote | — | — | 加工区→验证区→正式库 |
| 区退回 | POST /v1/halls/demote | — | — | 验证区→加工区 |
| 反馈记录 | POST /v1/playbooks/{id}/feedback | kairos_feedback_memory | — | Playbook outcome 记录 |
| Playbook 创建 | POST /v1/playbooks | — | — | 升华 strategy 产出 |
| 外部校准 | POST /v1/calibrate | kairos_calibrate | S-11 | 见证锚定更新 |
| 宪法管理 | POST /v1/constitution | — | S-11（唯一入口） | 宪法级偏好查看/修订 |
| 强制冻结 | POST /v1/freeze | — | 最高级 | 冻结所有内部环 |
| 降级切换 | POST /v1/degradation/switch | — | — | 保守静默/受限交叉验证/安全休眠 |
| 审计查询 | GET /v1/audit-log | — | — | HMAC 链完整性验证 |
| 证伪查询 | GET /v1/falsification | — | — | 耦合/VAD/聚合审计 |
| 后台维护 | POST /v1/maintenance/run | — | — | Light/Deep 模式 |
| 维护状态 | GET /v1/maintenance/status | — | — | |
| 端云同步推送 | POST /v1/sync/push | — | — | 本地→服务端增量 |
| 端云同步拉取 | POST /v1/sync/pull | — | — | 服务端→本地增量 |
| 快照导出 | POST /v1/sync/export | — | S-07（脱敏） | .kairos 格式 |
| 快照导入 | POST /v1/sync/import | — | — | 差异化合并 |
| 宪法解释层复审 | — | — | — | P6 合规/判例过期检查 |
| 后台 Diff 扫描 | — | — | — | 差异检验批量执行 |
| 热度衰减 | 自动（Light 模式） | — | — | α=0.95 |
| 冗余合并 | 自动（Light 模式） | — | S-14 | cos > 0.92 合并 |
| 实体提取 | 自动（Deep 模式） | — | — | LLM 批量提取 |
| TMT 补扫 | 自动（Deep 模式） | — | — | L2→L3→L4 逐级 |
| P6 合规扫描 | 自动（Deep 模式） | — | — | 压缩比余量监控 |
| 事实新鲜度过期扫描 | 自动（Deep 模式） | — | — | valid_until→expired→stale |

## 四、按阶段统计

| 阶段 | 操作数 | 说明 |
|:-----|:------:|:------|
| ENC | 7 | 创建/摄入 |
| RET | 15 | 检索/查询/报告 |
| STR | 31 | 更新/治理/运维/自动 |
| **总计** | **53** | |

> **对应关系**：本目录的 53 项操作与 feature-list.md 的 101 项功能之间存在多对多映射——一项功能可对应多种调用方式（API + Tool + CLI），一项操作也可服务于多项功能。操作目录回答"系统能执行什么指令"，功能清单回答"系统对外提供什么能力"。
