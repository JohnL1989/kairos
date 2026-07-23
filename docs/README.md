---
title: Kairos 文档索引
aliases:
  - 文档目录
  - 文档体系
tags:
  - kairos
  - documentation
created: 2026-07-18
updated: 2026-07-22
status: draft
---

# Kairos 文档索引

> **当前状态**：**文档草稿阶段，无运行代码**。本文档库尚无可运行的完整 Kairos 系统（注：`amber/` 目录下存在实验性引擎原型代码，用于概念验证，非生产实现）。feature-list 列出的 **101 项能力（43 核心 + 58 扩展；traceability-map 追溯其中 43 项与认知声明的映射）** 处于架构就绪状态，核心引擎代码未启动。

> **快速入口：** [系统架构](foundation/architecture-v1.0.0.md) · [认知基础](foundation/cognitive-foundation.md) · [待实现债务清单](governance/debt-collection.md)

---

## 地基文档（为什么 + 是什么）

| 路径 | 内容 |
|:-----|:-----|
| [`foundation/cognitive-foundation.md`](foundation/cognitive-foundation.md) | **认知基础** — 「记忆即使用」第一性原理、五轴度量空间（v1.0 承载四轴 + 可及性代理）、P1–P6 原则 |
| [`foundation/architecture-v1.0.0.md`](foundation/architecture-v1.0.0.md) | **系统架构** — 六层栈、监督平面、全部机制规格。全体系以本文为设计权威 |
| [`foundation/design-philosophy-relations.md`](foundation/design-philosophy-relations.md) | **理念关系图** — 七级排序/P1–P6/分域真理观等约束与协作关系 |

## 规格文档（具体长什么样）

| 路径 | 内容 |
|:-----|:-----|
| [`specification/claim-implementation-matrix.md`](specification/claim-implementation-matrix.md) | **声明-承载对齐矩阵** — 从认知基础提取的 37 项架构承载声明对应表 |
| [`specification/feature-list.md`](specification/feature-list.md) | **功能清单** — 12 类 **101 项**对外能力枚举 |
| [`specification/data-model.md`](specification/data-model.md) | **数据模型** — 31 张表 Schema + 索引 |
| [`specification/api-spec.md`](specification/api-spec.md) | **接口规格** — REST API / Agent Tool / CLI / 事件总线 |
| [`specification/implementation-map.md`](specification/implementation-map.md) | **实现映射** — 40+ 组件路径映射，从架构到代码模块 |
| [`specification/detailed-design.md`](specification/detailed-design.md) | **详细设计** — 核心组件状态机 + 算法伪代码 |
| [`specification/nfr-specification.md`](specification/nfr-specification.md) | **NFR 规格** — 性能/容量/可用性/资源/安全量化指标 |
| [`specification/requirements-baseline.md`](specification/requirements-baseline.md) | **需求基线** — 功能需求/NFR/约束/部署规模/能力梯度/RTM 表/版本边界 |
| [`specification/system-context.md`](specification/system-context.md) | **系统上下文** — 边界声明 + 外部依赖 |
| [`specification/use-cases.md`](specification/use-cases.md) | **使用场景** — 8 个典型交互场景 |
| [`specification/rl-weight-spec.md`](specification/rl-weight-spec.md) | **RL 权重优化器规格** — 六维权重（含 entity_boost）+ 学习算法 |
| [`specification/operation-catalog.md`](specification/operation-catalog.md) | **操作目录** — 53 项标准操作，按 ENC/RET/STR 三阶段组织，标注安全红线 |

## 开发文档（怎么上手开发）

| 路径 | 内容 |
|:-----|:-----|
| [`development/technology-stack.md`](development/technology-stack.md) | **技术选型全景** — Python/Litestar/PostgreSQL/pgvector |
| [`development/development-setup.md`](development/development-setup.md) | **开发环境搭建** — 本地开发步骤 + IDE 配置 |
| [`development/coding-conventions.md`](development/coding-conventions.md) | **开发规范** — 命名/结构/错误处理/日志 |
| [`development/integration-design.md`](development/integration-design.md) | **集成设计** — Agent 全生命周期 + 并发/超时/错误传播 |

## 治理文档

| 路径 | 内容 |
|:-----|:-----|
| [`governance/adr.md`](governance/adr.md) | **架构决策记录** — 10 项已采纳 ADR |
| [`governance/debt-collection.md`](governance/debt-collection.md) | **追缴清单** — 已闭环项 + 待实现债务路线图 |
| [`governance/risks.md`](governance/risks.md) | **风险登记册** — 架构风险与哲学张力 |
| [`governance/project-plan.md`](governance/project-plan.md) | **项目计划** — 4 Phase 里程碑（具体周数待代码启动后定） |
| [`governance/changelog.md`](governance/changelog.md) | **变更日志** — 语义化版本变更记录 |
| [`governance/social-calibration-roadmap.md`](governance/social-calibration-roadmap.md) | **社会性校准演进路线图** — v1.0→v2.0 里程碑 |
| [`governance/cognitive-architecture-gap.md`](governance/cognitive-architecture-gap.md) | **认知-架构承诺差距表** — 12 项降维/预留/偏离追踪 |
| [`governance/documentation-governance.md`](governance/documentation-governance.md) | **文档治理规范** — 更新联动/交叉引用/状态管理/编号注册 |
| [`governance/release-guide.md`](governance/release-guide.md) | **发布指南** — 版本号/检查清单/发布步骤/许可证 |

## 运维文档

| 路径 | 内容 |
|:-----|:-----|
| [`ops/deployment.md`](ops/deployment.md) | **部署指南** — 三级部署规模（轻量/标准/全量）+ 三级能力梯度（全量/标准/内核），环境变量、Docker 参考 |
| [`ops/configuration.md`](ops/configuration.md) | **配置参数参考** — 94 项参数 + 动态调参规则 |
| [`ops/reliability.md`](ops/reliability.md) | **可靠性策略** — RTO/RPO、备份、WAL 归档、LLM 熔断 |
| [`ops/observability.md`](ops/observability.md) | **可观测性设计** — 指标/日志/告警/检测器可见性 |
| [`ops/troubleshooting.md`](ops/troubleshooting.md) | **故障排查** — 常见问题与恢复命令 |
| [`ops/runbook.md`](ops/runbook.md) | **运维手册** — 日常操作/备份/升级/故障应急 |

## 质量文档

| 路径 | 内容 |
|:-----|:-----|
| [`quality/test-strategy.md`](quality/test-strategy.md) | **测试策略** — 单元/集成/E2E 三级 + 安全红线验证 |
| [`quality/acceptance-criteria.md`](quality/acceptance-criteria.md) | **验收标准** — 6 项债务完成条件 + 发布检查项 |
| [`quality/benchmark-plan.md`](quality/benchmark-plan.md) | **性能基准计划** — 延迟/吞吐/磁盘/回归阈值 |
| [`quality/test-plan.md`](quality/test-plan.md) | **测试计划** — 核心路径用例 + E2E + 测试数据 |

## 安全文档

| 路径 | 内容 |
|:-----|:-----|
| [`security/threat-model.md`](security/threat-model.md) | **威胁模型** — STRIDE + LLM 攻击面 + S-01~S-19 + HMAC 审计链 |
| [`security/security-specification.md`](security/security-specification.md) | **安全规格** — 安全需求/认证/加密/隐私/密钥/事件响应 |

## 用户文档

| 路径 | 内容 |
|:-----|:-----|
| [`user/quick-start.md`](user/quick-start.md) | **快速入门** — 5 分钟最小闭环教程 |
| [`user/user-guide.md`](user/user-guide.md) | **用户指南** — 上手/核心操作/最佳实践/限制 |

## 参考文档

| 路径 | 内容 |
|:-----|:-----|
| [`references/glossary.md`](references/glossary.md) | **术语表** — ~52 条中英文术语对照 |
| [`references/error-reference.md`](references/error-reference.md) | **错误参考** — 9 类 38 个错误码 |
| [`references/traceability-map.md`](references/traceability-map.md) | **需求可追溯性映射表** — 43 能力↔37 声明↔100 追踪项（27 闭环 DC + 62 MNM + 11 待实现 D）↔12 差距交叉映射 |
| [`references/usage-load-algorithm.md`](references/usage-load-algorithm.md) | **使用负载计量算法** |
| [`references/vad-coordinate-algorithm.md`](references/vad-coordinate-algorithm.md) | **VAD 情感坐标算法** |
| [`references/value-dimension-entropy.md`](references/value-dimension-entropy.md) | **价值维度熵值守护算法** |

## 评审文档

| 路径 | 内容 |
|:-----|:-----|
| [`reviews/architecture-audit-template.md`](reviews/Kairos架构文档审计模板_精简版.md) | **架构文档审计模板** — 独立评审提示词 |
| [`reviews/comprehensive-audit-report.md`](reviews/Kairos文档全集_Linus风格批判_主审终稿_2026-07-22.md) | **Linus 审计主审终稿** — 第三方全量审查 |
| [`reviews/comprehensive-audit-report.md`](reviews/Kairos文档全集_Linus风格批判_主审终稿_2026-07-22.md) | **文档全集审计报告（Linus 风格·主审终稿）** — 一致性/完整性/治理合规性 |
| [`reviews/architecture-analysis.md`](reviews/mnemosyne-os-cross-analysis.md) | **架构方案评审** — 四维分析 + 改造措施 + 实施路线图 |

---|---

总计：52 份文档**（foundation 3 + specification 12 + development 4 + governance 9 + ops 6 + quality 4 + security 2 + user 2 + references 6 + reviews 3 + README 1）**。其中 `foundation/architecture-v1.0.0.md` 为核心架构规格（全体系以架构文档为设计权威）。

## 阅读建议

| 目标 | 路径 |
|:-----|:-----|
| 理解 Kairos 是什么 | `README.md`（根目录自述）|
| 理解认知基础 | `foundation/cognitive-foundation.md` §1 → §2 |
| 理解系统架构 | `foundation/architecture-v1.0.0.md` 全文 |
| 查看待实现项 | `governance/debt-collection.md` |
| 部署运行 | `ops/deployment.md` |
| 配置系统 | `ops/configuration.md` |
| 编写代码 | `specification/implementation-map.md` → `development/coding-conventions.md` |
