---
title: 文档治理规范
aliases:
  - 文档维护规则
  - doc-governance
tags:
  - kairos
  - governance
  - documentation
created: 2026-07-21
updated: 2026-07-21
status: draft
---

# 文档治理规范

> 三轮审计反复发现"改了 A 没改 B"的根因。本文定义文档维护的元规则，防止文档腐烂。

---

## §1 更新联动规则

修改以下任一资产时，必须同步更新右侧文档：

| 修改对象 | 必须同步的文档 |
|:--------|:--------------|
| 架构设计（层/组件/接口） | `architecture-v1.0.0.md`、`implementation-map.md` |
| 数据模型（表/列/索引） | `data-model.md`、`api-spec.md` |
| API 端点（新增/变更/废弃） | `api-spec.md`、`integration-design.md`、`user-guide.md` |
| 配置参数（新增/删除/默认值变更） | `configuration.md`、`deployment.md`、`coding-conventions.md` |
| 功能清单（新增/删除功能） | `feature-list.md`、`claim-implementation-matrix.md` |
| 非功能指标（阈值/容量/RTO） | `nfr-specification.md`、`reliability.md` |
| 安全红线（新增/修订） | `architecture-v1.0.0.md §8`、`threat-model.md`、安全规格文档 |
| 测试用例（新增场景） | `test-strategy.md`、`test-plan.md`（用例库） |
| CLI 命令（新增/变更） | `api-spec.md` CLI 表、`quick-start.md`、`user-guide.md` |

**自行检查**：每次 commit 前运行 `grep -rn "旧值\|旧名" docs/` 确保无旧值残留。

---

## §2 交叉引用规范

1. 引用同一文档内的章节：用 `§X.Y`（形如 `§3.2`、`§0.5`）
2. 引用跨文档章节：用 `[文档名](相对路径) §X`
3. 引用认知基础→架构：一律使用词汇桥接表（architecture §0.6）中的映射
4. 禁止引用不存在的章节号——新增或重排章节后必须 grep 全库更新所有交叉引用

**死链检测**：每次里程碑前运行 `grep -rn '§\d\+\.\d\+' docs/` 逐一核实目标是否存在。

---

## §3 审查周期

| 周期 | 审查内容 |
|:----|:---------|
| 每次代码 commit | 关联文档是否同步更新（§1 联动表） |
| 每次里程碑（Phase 交付） | 全库交叉引用死链检测 + 跨文档数值一致性检查 |
| 每月 | 全量文档状态审计（draft → final 晋升 / 废弃标记） |
| 每次外部评审接收后 | 评审建议逐条回复并更新对应文档 |

---

## §4 状态管理

> **当前阶段声明**：代码启动前，全部文档保持 `draft` 状态。晋升至 `final` 的规则待代码启动后执行。此暂缓不改变治理规则的效力——规则在代码启动后即刻生效。

| 状态 | 含义 | 晋升条件 |
|:----|:-----|:---------|
| `draft` | 初稿/未定稿，内容可能不完整 | 完成自审 + 至少一轮外部审阅 |
| `v1.0.0` | 与当前草稿完善阶段一致，可依赖 | 与 architecture-v1.0.0.md 无矛盾 |
| `deprecated` | 已被替代，仅保留历史参考 | 新文档已发布，旧文档标记废弃原因和替代路径 |

---

## §5 编号与命名注册

以下命名空间在各自文件中维护，新增或变更必须先注册再使用：

| 命名空间 | 注册位置 | 格式 |
|:--------|:--------|:----|
| 功能编号（W/R/M/SF/F/PM/C/A） | `feature-list.md` 功能分类统计 | 分类前缀 + 两位数序号 |
| 安全红线编号（S-01~S-19） | `architecture-v1.0.0.md §8` | S-两位数 |
| S-20~S-22（v2.0 多 Agent 校准扩展） | `social-calibration-roadmap.md` | S-两位数 |
| 闭环编号（DC-XXX） | `governance/debt-collection.md` | DC-三位数 |
| Mnemosyne 闭环编号（MNM-XXX） | `governance/debt-collection.md` | MNM-三位数 |
| 能力缺口编号（G-XXX） | `governance/cognitive-architecture-gap.md` | G-两位数 |
| 社会性校准里程碑编号（SCR-XXX） | `governance/social-calibration-roadmap.md` | SCR-两位数 |
| 测试用例编号（TC-XXX） | `quality/test-plan.md` | TC-前缀 + 两位数 |
| 错误码（ERR-XXX-NNN） | `references/error-reference.md` | ERR-XXX-NNN |
| 债务编号（D-001~D-211） | `governance/debt-collection.md` | D-三位数 |
| 风险编号（R-001~R-NNN） | `governance/risks.md` | R-三位数 |

**禁止**：同一名称出现在两处不同定义的文档中。若必须引用，加注 `（见 §X）` 指向唯一事实源。

---

## §6 单一事实源原则

1. 每个数值/枚举/命名**只有一个定义位置**
2. 其他文档引用该值时使用交叉引用，不重复写值
3. 例外：版本记录中的历史描述不受此限（记录已发生的事实）
4. 违反即标记为「数据漂移」，在下次审查中修复

---

## 版本记录

| 版本 | 日期 | 变更 |
|:----|:----|:-----|
| v1.0.0 | 2026-07-21 | 初始版本。更新联动表、交叉引用规范、审查周期、状态管理、编号注册、单一事实源原则 |
