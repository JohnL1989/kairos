---
title: 文档目录
aliases:
  - 文档索引
  - Kairos 文档
tags:
  - kairos
  - documentation
created: 2026-07-18
updated: 2026-07-20
status: v1.0.0
---

# Kairos 文档目录

> Kairos（καιρός）——在正确的时机做正确的事。记忆的价值不在「记住了什么」，而在「在正确的时机以正确的方式用到」。
>
> **快速入口：** 架构设计 → `kairos/architecture-v1.0.0.md` | 全部待实现项 → `kairos/governance/debt-collection.md`

---

## Kairos 文档

| 路径 | 功能 | 篇幅 |
|:----|:-----|:----:|
| `kairos/architecture-v1.0.0.md` | **系统架构**——唯一事实来源。六层架构、四类契约、路径空间、升华管道 | ~1240 行 |
| `kairos/cognitive-foundation.md` | **认知基础**——记忆即使用。四轴度量空间、P1–P6 原则、辞典式排序、分域真理观 | ~490 行 |
| `kairos/governance/adr.md` | **架构决策记录**——10 项已采纳决策 | — |
| `kairos/governance/debt-collection.md` | **追缴清单**——26 项已闭环 + 6 项代码债务路线图 | — |
| `kairos/governance/risks.md` | **风险登记册**——架构风险与哲学张力 | — |
| `kairos/governance/social-calibration-roadmap.md` | **社会性校准演进路线图**——v1.0→v2.0 里程碑 | — |
| `kairos/governance/project-plan.md` | **项目计划**——4 Phase × 12 周里程碑 | — |
| `kairos/governance/changelog.md` | **变更日志**——语义化版本变更记录 | — |
| `kairos/design/design-philosophy-relations.md` | **理念关系图**——七级排序/P1–P6/分域真理观等约束与协作关系 | — |
| `kairos/design/claim-implementation-matrix.md` | **声明-承载对齐矩阵**——37 项认知声明与架构承载版本对应表 | — |
| `kairos/design/feature-list.md` | **功能清单**——41 项对外能力枚举 | — |
| `kairos/design/data-model.md` | **数据模型设计**——7 张核心表 Schema + 索引 | — |
| `kairos/design/api-spec.md` | **接口规格书**——REST API / Agent Tool / CLI / 事件总线格式 | — |
| `kairos/design/technology-stack.md` | **技术选型全景**——Python/Litestar/PostgreSQL/pgvector 版本约束 | — |
| `kairos/design/coding-conventions.md` | **开发规范**——命名/结构/错误处理/日志 | — |
| `kairos/design/nfr-specification.md` | **NFR 规格**——性能/容量/可用性/资源/安全量化指标 | — |
| `kairos/design/use-cases.md` | **使用场景**——8 个典型交互场景 | — |
| `kairos/design/integration-design.md` | **集成设计**——Agent 全生命周期 + 并发/超时/错误传播 | — |
| `kairos/design/system-context.md` | **系统上下文**——边界声明 + 外部依赖 | — |
| `kairos/design/development-setup.md` | **开发环境搭建**——本地开发步骤 + IDE 配置 | — |
| `kairos/ops/deployment.md` | **部署指南**——双模式部署、环境变量、Docker 参考 | — |
| `kairos/ops/reliability.md` | **可靠性策略**——RTO/RPO、备份、恐慌模式、LLM 熔断 | — |
| `kairos/ops/troubleshooting.md` | **故障排查**——常见问题与恢复命令 | — |
| `kairos/ops/configuration.md` | **配置参数参考**——60 项参数 + 动态调参规则 | — |
| `kairos/references/usage-load-algorithm.md` | **五类负载计量算法** | — |
| `kairos/references/vad-coordinate-algorithm.md` | **VAD 情感坐标算法** | — |
| `kairos/references/value-dimension-entropy.md` | **价值维度熵值守护算法** | — |
| `kairos/quality/test-strategy.md` | **测试策略**——单元/集成/E2E 三级 + 安全红线验证项 | — |
| `kairos/quality/acceptance-criteria.md` | **验收标准**——6 项债务完成条件 + 发布检查项 | — |
| `kairos/quality/benchmark-plan.md` | **性能基准计划**——延迟/吞吐/磁盘/回归阈值 | — |
| `kairos/ops/observability.md` | **可观测性设计**——指标/日志/告警/检测器可见性 | — |
| `kairos/references/error-reference.md` | **错误参考**——7 类 30 个错误码完整展开 | — |
| `kairos/security/threat-model.md` | **威胁模型**——STRIDE 映射 + LLM 攻击面 + HMAC 审计链 | — |
| `kairos/user/user-guide.md` | **用户指南**——上手/核心操作/最佳实践/限制 | — |
| `kairos/user/quick-start.md` | **快速入门**——5 分钟最小闭环教程 | — |
| `kairos/reviews/cognitive-foundation-deep-analysis.md` | **认知基础深层分析**——15 轮评析精华汇总 | — |
| `kairos/reviews/cognitive-foundation-review-2026-07-20.md` | **认知基础第三轮评审**——三轮深度审校吸收模式 | — |
| `kairos/reviews/Kairos架构文档审计模板_精简版.md` | **审计模板**——11 维度架构文档评分框架 | — |

## 归档参考

| 路径 | 说明 |
|:----|:-----|
| `aion/architecture-v1.0.0.md` | **Aion-Memory 系统架构（已归档）**。Kairos 追缴清单中多项实现细节的参考来源 |

---

## 阅读建议

| 目标 | 路径 |
|:----|:-----|
| 理解认知基础 | `kairos/cognitive-foundation.md` §1 → §2 |
| 理解 Kairos 设计哲学 | `kairos/architecture-v1.0.0.md` §0 → §1 |
| 理解 Kairos 全貌 | `kairos/architecture-v1.0.0.md` 全文 |
| 审查已做的架构决策 | `kairos/governance/adr.md` |
| 查看待实现项 | `kairos/governance/debt-collection.md` |
| 了解架构风险 | `kairos/governance/risks.md` |
| 部署运行 | `kairos/ops/deployment.md` + `kairos/ops/reliability.md` |
| 配置系统 | `kairos/ops/configuration.md` |
| 理解功能范围 | `kairos/design/feature-list.md` |
| 查看数据模型 | `kairos/design/data-model.md` |
| 查看接口规格 | `kairos/design/api-spec.md` |
| 了解测试策略 | `kairos/quality/test-strategy.md` |
| 查看验收标准 | `kairos/quality/acceptance-criteria.md` |
| 查看性能基准 | `kairos/quality/benchmark-plan.md` |
| 查看可观测性 | `kairos/ops/observability.md` |
| 查看项目计划 | `kairos/governance/project-plan.md` |
| 了解技术选型 | `kairos/design/technology-stack.md` |
| 编写代码（规范） | `kairos/design/coding-conventions.md` |
| 排查问题 | `kairos/ops/troubleshooting.md` |
| 了解安全设计 | `kairos/security/threat-model.md` |
| 查阅算法参考 | `kairos/references/` |
| 查阅 Aion 实现细节（归档参考） | `aion/architecture-v1.0.0.md` |

---

## 文档引用规则

1. **架构文档是唯一事实来源**——所有文档以 `kairos/architecture-v1.0.0.md` 为准
2. 跨文档引用使用相对路径（`kairos/ops/deployment.md`）
3. 新增文档须在本 README 中注册入口
4. 归档文档不参与引用链——Aion 文档仅作参考，不作为决策依据
