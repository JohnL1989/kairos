---
title: Kairos 变更日志
aliases:
  - CHANGELOG
tags:
  - kairos
  - governance
  - changelog
created: 2026-07-20
updated: 2026-07-23
status: draft
---

# CHANGELOG

> **定位**：按日期记录的变更日志，记录从什么变成什么。各文档内嵌的版本记录保留为文档级审计，CHANGELOG 提供跨文档的版本演进全景。

---

## v1.0.0（2026-07-23）— R15 全量审计修复

### Phase 0：止血

- README L152 "代码仓库为空" → 承认 `amber/` 代码存在（main.py 734行 + API 19模块 + schema 449行）
- 计数统一：99→101 项能力（9处），11/18→31 张表（2处），S-01~S-19 连续编号确认
- 虚拟校准置信度上限统一为 0.3（L2058 0.6→0.3）
- 参数命名统一：VIRTUAL_MERGE_THRESHOLD→VIRTUAL_CALIBRATION_SIMILARITY_THRESHOLD，VIRTUAL_FAILURE_COUNT→VIRTUAL_CALIBRATION_CONFLICT_THRESHOLD
- SQLite 路径统一：轻量模式 ~/.kairos/kairos.db，标准模式 PostgreSQL DSN 配置
- 全量 grep 清扫零残留

### Phase 1：枚举统一

- 记忆状态两轴正交化（stage/status/hall），cognitive-foundation 表加"所属轴"列
- relation_type 统一：api-spec 删 "mentions" 幽灵值，feature-list 补 part_whole
- RL 权重维度名统一：explicit_feedback → user_feedback
- 事件枚举权威源落地：architecture §10.10 为唯一权威

### Phase 2：DDL 与 API 契约

- 新增 db/schema.sql（29 表 / 524 行 PostgreSQL DDL）
- memory_entities UNIQUE(memory_id,entity_id,valid_from) 修复时序图谱
- user_profiles PK → (user_id, trait_type) 复合主键
- audit_log HMAC 覆盖 target_id + details
- api-spec §6.4 补回（重编号 6.5→6.4）
- 幽灵端点正式定义（search/heat-top/feedback/stats）
- expire/lock/merge/path-suppress + kairos_merge 工具正式注册
- PM-01/02 标记 ⏳ v1.1+，新增 DC-027 追踪

### Phase 3：治理重建

- 旧 Linus 审查 120+ 条发现按 10 大断裂带聚合为 meta-debt（DC-029~DC-031）
- 62 条 MNM 标记"追踪闭环"（非"验证闭环"），加注验收判据缺失
- cognitive-architecture-gap 12 条差距补收敛判据（G-01~G-12）
- release-process 改为 release-guide（意图声明文档）
- documentation-governance §1 联动表缺省状态标注

### 变更文件

15 份文档 + 1 个新文件（db/schema.sql），约 50+ 处独立修改。

---

## v1.0.0-rc.1（2026-07-22）

**Kairos 跨项目能力吸收阶段（43→101 项能力）**
- 跨项目吸收 EchoMind/Mnemosyne/MemOS 等 5 系统
- 新增 58 项扩展能力
- 治理体系建立（debt-collection/risks/project-plan）

## v1.0.0-rc.0（2026-07-20）

**初始设计冻结**
- 认知基础 + 架构文档双核心定型
- 43 项核心能力基线
- 19 条安全红线（S-01~S-19）
- 框架文档体系 52 份 + 治理三件套
