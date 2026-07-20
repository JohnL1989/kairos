# Kairos (καιρός)

**AI 智能体的记忆基础设施——合时之忆，恰如其分。**
*Use-defined memory with four-axis metric space and contract-driven lifecycle.*

---

## 定位 · About

**Kairos（καιρός，希腊语「恰当的时机」）** 是为 AI 智能体设计的认知记忆系统。核心理念：**记忆的价值由使用定义**——而非存储时长、来源权威或人为优先级。

Kairos (καιρός, the ancient Greek word for "the right, critical moment") is a cognitive memory system for AI agents, architected on the principle that **memory value is defined by use**—not by storage duration, source authority, or arbitrary priority.

Unlike traditional key-value stores or vector databases, Kairos treats memory as a **multi-dimensional cognitive space**:

| 概念 · Concept | 含义 · Meaning |
|:--------------|:--------------|
| **四轴度量空间** · Four-axis metric space | 使用价值 · Usage value, 见证价值 · Witness value, 时间轴 · Temporal axis, 认知完整性 · Cognitive integrity |
| **契约驱动生命周期** · Contract-driven lifecycle | 每条记忆的存留/检索/遗忘由使用契约决定（常驻/按需/环境/临时） |
| **激活-存储解耦** · Activation-storage decoupling | 激活决策属策略层，存储属存储层——互不耦合 |
| **辞典式排序** · Lexicographic ordering | 身份 > 探索 > 宪法 > 校准 > 认知完整性 > 时间 > 间接度 |
| **价值独立性公理** · Value independence axiom | "好用 ≠ 真实"——使用权重与见证锚定结构性冲突 |

## 阶段 · Status

当前：**设计冻结（v1.0.0）**——架构与设计已完整规格化，代码尚未启动。

Current: **Design freeze (v1.0.0)** — architecture and design fully specified, code not yet started.

```
Phase 0: 基建搭建 Infrastructure  (Weeks 1-2)
Phase 1: 核心存储 Core Storage   (Weeks 3-6)
Phase 2: 认知层 Cognitive Layer  (Weeks 7-10)
Phase 3: 集成验证 Integration    (Weeks 11-12)
```

## 文档 · Documentation

| 路径 Path | 说明 Description |
|:----------|:----------------|
| [`docs/architecture-v1.0.0.md`](docs/architecture-v1.0.0.md) | **系统架构**——六层栈 + 监督平面，唯一事实来源 |
| [`docs/cognitive-foundation.md`](docs/cognitive-foundation.md) | **认知基础**——"记忆即使用"，P1–P6 原则，四轴空间，分域真理观 |
| [`docs/design/feature-list.md`](docs/design/feature-list.md) | **功能清单**——8 类 43 项能力 |
| [`docs/design/data-model.md`](docs/design/data-model.md) | **数据模型**——7 张核心表 Schema + 索引 |
| [`docs/design/api-spec.md`](docs/design/api-spec.md) | **接口规格**——REST API / Agent Tool / CLI / 事件总线 |
| [`docs/user/quick-start.md`](docs/user/quick-start.md) | **快速入门**——5 分钟最小闭环教程 |
| [`docs/user/user-guide.md`](docs/user/user-guide.md) | **用户指南**——操作、最佳实践、限制 |
| [`docs/governance/project-plan.md`](docs/governance/project-plan.md) | **项目计划**——4 Phase × 12 周里程碑 |
| [`docs/governance/adr.md`](docs/governance/adr.md) | **架构决策记录**——10 项已采纳决策 |
| [`docs/governance/debt-collection.md`](docs/governance/debt-collection.md) | **追缴清单**——26 项已闭环 + 10 项待实现 |
| [`docs/ops/deployment.md`](docs/ops/deployment.md) | **部署指南**——双模式部署、环境变量、Docker |
| [`docs/ops/configuration.md`](docs/ops/configuration.md) | **配置参考**——64 项参数 + 动态调参规则 |
| [`docs/security/threat-model.md`](docs/security/threat-model.md) | **威胁模型**——STRIDE + LLM 攻击面 + HMAC 审计链 |
| [`docs/quality/test-strategy.md`](docs/quality/test-strategy.md) | **测试策略**——单元/集成/E2E 三级 + 16 条安全红线验证 |

## 设计哲学 · Design Philosophy

Kairos 从一条公理「**记忆即使用**」出发，推导出五条推论，约束全部架构决策：

Five corollaries derived from the axiom **"memory is use"**:

1. **使用定义价值** → 四轴度量空间 / Use defines value → Four-axis metric space
2. **不同记忆，不同契约** → 契约层 / Different memories, different contracts → Contract layer
3. **契约决定激活而非存储** → 统一 LTM / Contracts govern activation, not storage → Unified LTM
4. **遗忘是工程权衡** → 二维遗忘曲面 / Forgetting is engineering tradeoff → 2D forgetting surface
5. **探索是认知边界测绘** → 元认知探索预算 / Exploration is cognitive boundary mapping → Meta-cognitive budget

架构强制实施 **辞典式排序链**（身份 > 探索 > 宪法 > 校准 > 认知完整性 > 时间 > 间接度）作为宪法级不变量，同时通过沙箱验证环允许受控例外。

The architecture enforces a **Lexicographic Ordering Chain** as a constitutional invariant, while allowing controlled exceptions through a sandbox verification loop.

## 许可证 · License

版权所有 © 2026 李鸣 (JohnL1989)。保留所有权利。

Copyright © 2026 李鸣 (JohnL1989). All rights reserved.

详见 [LICENSE](LICENSE)。本项目非开源软件——允许查看和学习设计，任何其他用途须经书面授权。

See [LICENSE](LICENSE) for terms. This is not open-source software — viewing and studying the design is permitted; any other use requires explicit written permission.
