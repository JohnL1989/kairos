---
title: Kairos 术语表
aliases:
  - Glossary
  - 术语表
tags:
  - kairos
  - references
  - glossary
created: 2026-07-20
updated: 2026-07-20
status: draft
---

# Kairos 术语表

> **定位**：Kairos 系统关键术语中英文对照及定义。每条术语附源文档引用，方便追溯完整上下文。

**快速查阅**：使用 Ctrl+F 搜索术语名。定义源自 `foundation/architecture-v1.0.0.md`（架构）、`foundation/cognitive-foundation.md`（认知基础）或 `references/` 算法参考文档。算法参考术语（使用负载计量器、VAD 坐标、价值维度熵等）详见各自算法文档，本文不重复。

---

## 一、系统层级 System Levels

| 术语 | 英文 | 定义 | 来源 |
|:----|:-----|:-----|:-----|
| 宪法主权面 | Sovereignty Plane | 与 1–5 层正交的独立平面，接收外部校准信令。含宪法修订端口、强制冻结、虚拟校准生成器 | 架构 §1 |
| 元认知层 | Metacognition Layer | 监控、评估、调节下层行为。含检测器族、治理器族、自观察记忆、审计庭接口 | 架构 §2 |
| 策略层 | Strategy Layer (PM) | 记忆路由与协调层——预测器、调节器、价值上下文管理器、路径注册表 | 架构 §3 |
| 存储层 | Storage Layer | 统一长期记忆（LTM），含双副本、路径空间、升华管道、遗忘调度器、关系索引 | 架构 §5 |
| 工作记忆层 | WM Layer | 当前操作缓冲区——模拟隔离区、沙箱验证环、多路径融合、推理皮层 | 架构 §6 |
| 接入层 | Access Layer | 外部接口——REST API、CLI、Agent Tool、多源摄取、干扰控制 | 架构 §7 |
| 监督平面 | Supervision Plane | 独立审计与证伪监视器——审计庭、耦合计监测器、VAD 独立性测试器、体系聚合审计器 | 架构 §1.7 |

## 二、核心记忆概念 Core Memory

| 术语 | 英文 | 定义 | 来源 |
|:----|:-----|:-----|:-----|
| **五轴度量空间（v1.0 承载四轴，第五轴可及性以代理实现，完整度量 v1.1）** | Five-axis Metric Space (v1.0 carries four axes, fifth accessibility axis via proxy, full metric v1.1) | 使用价值/见证价值/时间/认知完整性四轴正交的度量空间，辅以潜伏势能。完整规范模型为五轴（含可及性轴），v1.0 以降维形式承载 | 认知基础 §1.1 |
| 多重记忆 | Multiple Memory | 同一经验可同时编码为情景/叙事/语义/程序四类，四类间有因果/独立/层级/竞争关系 | 认知基础 §1.2 |
| 潜伏势能 | Latent Potential | 零使用价值记忆的保留依据，由元认知层盲区探测触发重估 | 架构 §5.2 |
| 升华管道 | Sublimation Pipeline | raw→item→strategy→behavior 四阶段渐进提纯，空闲驱动 | 架构 §5.2 |
| 遗忘调度器 | Forgetting Scheduler | 基于二维遗忘曲面（去语境化程度×年龄）计算遗忘得分，触发归档 | 架构 §5.2 |
| 路径空间 | Path Space | 确定性检索手段，`kairos://` 格式，为第一检索入口，向量搜索退居辅助 | 架构 §5.2 |
| 关系索引 | Relation Index | 四类记忆关系（因果/部分独立/弱层级/竞争）+ 粒度关系（部分-整体）的独立索引空间 | 架构 §5.2 |

## 三、契约与激活 Contracts & Activation

| 术语 | 英文 | 定义 | 来源 |
|:----|:-----|:-----|:-----|
| 常驻契约 | Permanent | 核心规则/宪法级偏好，不参与遗忘评估（S-10 见证豁免保护） | 架构 §3.1 |
| 按需契约 | Ondemand | 日常写入默认选项，低使用权重时被遗忘 | 架构 §3.1 |
| 环境契约 | Environmental | 高相关信息（如当天上下文），环境变化时自然过期 | 架构 §3.1 |
| 临时契约 | Temporary | 中间状态/临时缓存，空闲时优先清理 | 架构 §3.1 |
| 激活-存储解耦 | Activation-Storage Decoupling | 契约决定激活策略而非存储位置——所有记忆统一管理，激活/检索/衰减策略因契约而异 | 认知基础 P3 |
| 意图契约 | Intention Contract | 前瞻记忆专用——位于 `kairos://_system/intentions/`，不受遗忘调度器评估 | 架构 §6.2 |
| 归档 | Archived | 系统被动——升华产物/低使用记忆从主存储移至冷存储，可复兴（关联检索触发） | 架构 §5.2 |
| 抑制 | Suppressed | 用户主动——定向遗忘操作标记，抑制检索但保留数据（软删除），可撤销 | api-spec §三 |
| 硬删除 | Delete | 用户主动——物理删除数据，仅用于临时契约，不可恢复 | api-spec §三 |

## 四、价值体系 Value System

| 术语 | 英文 | 定义 | 来源 |
|:----|:-----|:-----|:-----|
| 使用价值轴 | Usage Value Axis | 使用价值的多维特征空间——按目的性（检索/验证/贡献）、方式性（模拟/非模拟）、意识性（内隐/外显）区分 | 认知基础 §1.1 |
| 见证价值轴 | Witness Value Axis | 外部校准（符合论）+ 内部叙事自洽度（融贯论），同轴双层 | 认知基础 §1.1 |
| 时间轴 | Temporal Axis | 物理时间衰减 + 逻辑-因果时间（事件时序/因果关系/程序执行流）正交双轴 | 认知基础 §1.1 |
| 认知完整性轴 | Cognitive Integrity Axis | 反例锚点/死胡同路径/组合约束的结构性占位价值，`is_structure=true` 的记忆不参与遗忘 | 认知基础 §1.1 |
| 价值独立性公理 | Value Independence Axiom | "好用≠真实"——使用权重与见证锚定结构性冲突，非默认和谐 | 架构 §5.3 |
| 辞典式排序 | Lexicographic Ordering | 七级优先级链：身份>探索>宪法>校准>认知完整性>时间>间接度，宪法级不变量 | 架构 §3.2 |
| 见证锚定 | Witness Anchor | 存储层主副本——强一致性，不可篡改，含叙事自洽度字段 | 架构 §5.3 |
| 使用权重 | Usage Weight | 存储层影子副本——最终一致性，可演化，异步合并 | 架构 §5.3 |
| 差异检验 | Differential Check | 使用权重陡升时触发，判断是否需要更新见证锚定 | 架构 §5.5 |
| 分域真理观 | Domain Truth Pluralism | 常规操作→实用论，更新合并→融贯论，冲突校准→符合论；跨域冲突→辞典式排序兜底 | 认知基础 §2.1 |
| 保守倾向 | Conservative Bias | 平局→NO-OP，不确定→默认保守，跨域回退→规范真理 | 认知基础 §2.1 |

## 五、认知与演进 Cognitive & Evolution

| 术语 | 英文 | 定义 | 来源 |
|:----|:-----|:-----|:-----|
| 弱自反性 | Weak Self-Reflexivity | 系统认知真实性依赖外部校准供给，自反性上限受外部供给边界限定 | 认知基础 引论 |
| 他律性约束 | Heteronomy Constraint | 外部校准源充分性决定系统的认知天花板上限 | 认知基础 §三 |
| 惯性校准 | Inertial Calibration | 外部校准中断时系统依赖最后一次校准快照维持内部裁决基准 | 架构 §10.9 |
| 认知关节 | Cognitive Joint | 基于不确定认知所做的可拆卸可替换的设计决策点 | 认知基础 引论 |
| P6 方法论保障 | P6 Principle | 禁止无声丢失维度信息——任何标量化操作须保留多维表征可回溯性 | 认知基础 §2.3 |
| 身份条件与价值条件 | Identity vs Value Conditions | 记录的双轨约束——append-only 保障身份条件，使用权重决定价值条件 | 认知基础 B.1 |
| 种子锚点 | Seed Anchors | 冷启动参考物——`kairos://_system/seeds/`，遵循最小化/可复审/可替换三项约束 | 认知基础 B.2 |

## 六、工程组件 Engineering Components

| 术语 | 英文 | 定义 | 来源 |
|:----|:-----|:-----|:-----|
| 双副本分离 | Dual Copy Separation | 见证锚定（强一致）+ 使用权重（最终一致），S-14 语境自指禁令——内部信号不得作为见证锚定真实性的证据来源 | 架构 §5.3 |
| 事件总线 | Event Bus | 基于数据库表（events）的跨层异步通信机制，10 类事件，优先级 0–9 | 架构 §10.10 |
| 沙箱验证环 | Sandbox Verification Loop | WM 层新类型/新价值轴试运行→元审计确认→合并的验证机制 | 架构 §6.2 |
| 模拟隔离区 | Simulation Isolation Zone | WM 层反事实假设空间，模拟产物不可未经实证转正（S-13） | 架构 §6.2 |
| 推理皮层 | Reasoning Cortex | WM 子模块——常设最小推理内核，仅用于前瞻监控/事件排序/候选裁剪三类操作 | 架构 §6.2 |
| 健康计数器 | Health Counter | 元认知层独立旁路——仅监测环延迟/死锁/解释衰减，唯一权限触发降级信号 | 架构 §2.2 |
| 注意力调度器 | Attention Scheduler | 横切组件——统一管理全系统注意力资源分配、容量限制、动态调权 | 架构 §3.2 |

## 七、安全红线 Security Redlines

| 术语 | 英文 | 定义 | 来源 |
|:----|:-----|:-----|:-----|
| 安全红线 | Security Redlines | S-01~S-17 共 17 条不可降级的硬约束，违反即拒绝+审计日志记录 | 架构 §8 |
| 语境自指禁令（S-14） | Contextual Self-Reference Prohibition | 内部信号不得作为见证锚定真实性的证据来源——使用权重不可无声改写见证锚定 | 架构 §8 |
| 审计链 | Audit Chain | 双字段链式审计日志——`(a)` 明文链 `prev_content_hash`（供按内容追踪），`(b)` HMAC-SHA256 完整性签名 `hmac(n) = HMAC(key, timestamp+operator+action+content_hash+prev_hmac)`。同时支持精确定位篡改记录和整体完整性校验 | 架构 §10.10 |
| 证伪响应 | Falsification Response | 体系聚合可证伪性的架构承载——耦合计监测器 + VAD 独立性测试器 + 聚合审计器 | 架构 §10.10 |

---

## 版本记录

| 版本 | 日期 | 变更 |
|:----|:----|:-----|
| v1.0.0 | 2026-07-20 | 初始术语表。7 类约 52 条术语，含来源引用与交叉关联。算法参考术语（使用负载计量器/VAD 坐标/价值维度熵）另见各自算法文档。 |
