# Kairos（καιρός）

**AI 智能体的认知记忆基础设施——合时之忆，恰如其分。**
*Cognitive memory infrastructure for AI agents — the right memory at the right moment.*

> Kairos（καιρός，古希腊语「恰当的时机」）——记忆的价值不在于「记住了什么」，而在于「在正确的时机以正确的方式用到」——并且知道什么时候自己不知道。

![Status](https://img.shields.io/badge/status-draft-yellow) ![Capabilities](https://img.shields.io/badge/capabilities-99-blue) ![License](https://img.shields.io/badge/license-MIT-green)

---

## 一、概览 · Overview

Kairos 是一个为 AI 智能体设计的**认知记忆系统**。不同于传统键值存储或向量数据库，Kairos 将记忆建模为**多维认知空间**——不仅记录「发生过什么」，还追踪每段记忆的使用模式、见证可信度、时间结构与认知结构占位价值。

核心职责：记忆的存储、组织、检索、遗忘与升华。同时携带最小推理回路（推理皮层）以承载前瞻保持、使用事件驱动更新与跨层信号路由——使 Kairos 的架构边界从「纯记忆中间件」扩展到「携带最小推理回路的记忆系统」。

| 指标 | 数值 |
|:-----|:-----|
| 架构层次 | 7 层 |
| 能力维度 | 12 类 99 项 |
| 数据表 | 18 张核心表 |
| 安全红线 | 19 条（S-01~S-19） |
| 文档体系 | 52 份 |

---

## 二、架构全景 · Architecture

```
┌─────────────────────────────────────────────────────┐
│  ① 宪法主权面 (§1)  S-01~S-19  19条安全红线         │
│  ├─ 政治层：身份优先级 > 一切                       │
│  ├─ 法律层：七级辞典式排序                          │
│  ├─ 宪法解释层：P1–P6 原则仲裁                      │
│  └─ 监督平面：HMAC 审计链                           │
├─────────────────────────────────────────────────────┤
│  ② 元认知层 (§2)  检视器 + 告警器 + 校准器          │
│  └─ 系统对自身的周期性检视与自适应校准               │
├─────────────────────────────────────────────────────┤
│  ③ 策略层 (§3)  注意力调度 + 价值上下文              │
│  └─ 编码/巩固/检索三环节的注意力预算分配              │
├─────────────────────────────────────────────────────┤
│  ④ 推理皮层 (§4)  轻量本地推理 / 汇聚式多路径融合    │
├─────────────────────────────────────────────────────┤
│  ⑤ 存储层 (§5)  双副本隔离 · 30+ 核心组件            │
│  ├─ 混合检索(6维：语义+BM25+时序+信任+热度+实体)     │
│  ├─ 实体知识图谱 + 时序窗口 + 社区检测               │
│  ├─ 升华管道(L0→L4) + 符号化压缩                    │
│  ├─ 三级技能进化(Playbook→World Model→Skills)        │
│  ├─ RL优化器 + 提示词优化器 + 自反思元记忆优化        │
│  ├─ 临时事实智能过期 + 记忆版本管理                   │
│  └─ 事实新鲜度 + 交叉编码器重排 + 图谱距离重排       │
├─────────────────────────────────────────────────────┤
│  ⑥ 工作记忆层 (§6)  槽位 + WM-Support协同            │
├─────────────────────────────────────────────────────┤
│  ⑦ 接入层 (§7)  MCP Bridge · Memory Provider         │
│  └─ 12工具集 / Clarify消歧 / Reflect按需分析          │
└─────────────────────────────────────────────────────┘
```

---

## 三、设计哲学 · Design Philosophy

### 核心公理

> **「记忆即使用」——以使用为衡量是价值条件（评价标尺），而非存在论断言（存在理由）。**

「使用」涵盖两种异质的激活活动：
- **工具性使用**：服务于已知目标下的检索/验证/贡献/模拟
- **认识论使用**：服务于认知边界测绘（探索），价值在活动发生前不可被评估

### 第一性原理链

```
认知（是什么）→ 理念（为什么）→ 架构（怎么做）→ 上限（天花板在哪）
```

正向链驱动设计，逆向链暴露认知边界。不确定决策标记为「认知关节」，可拆卸、可替换。

### 设计原则 P1–P6

- **P1 · 条件正确性**——在约束条件下，做相对最优决策而非绝对正确
- **P2 · 信息自由原则**——数据管线各环节完整传递特定字段（记忆类型、命名空间）
- **P3 · 无损分离原则**——可分离的功能必须分离，可共享的表达必须共享
- **P4 · 速度保真原则**——使用路径必须比见证路径快，见证路径必须比使用路径完整
- **P5 · 不可稀释原则**——P6 维度的任何子维度在记忆写入全过程中不被衰减或丢失
- **P6 · 结构完整性守护**——标记 `is_structure=true` 的记忆不受遗忘调度器影响

---

## 四、核心能力 · Core Capabilities（99 项）

| 类别 | 项数 | 内容概要 |
|:-----|:----:|:---------|
| **记忆检索** | **17** | 6维混合排序/图谱距离/Cross-encoder/时序查询/实体加成/BM25词形归并/递归路径检索 |
| 系统管理 | 20 | 跨平台身份/检索轨迹可视化/主动话题/纠正检测/批量和事务 |
| 记忆管理 | 14 | 状态机四态/社区检测/版本管理/临时过期/差分索引/冲突解决 |
| 升华管道 | 13 | L0-L4蒸馏/符号化压缩/Playbook/提示词优化/自反思元记忆优化/Reflect |
| 记忆写入 | 12 | 捕获门控/权限检验/秘密检测/差异检验/批量事务 |
| RL优化 | 4 | Cosine LR/ε-greedy/RCW/KPop/历史基线 |
| Playbook | 4 | 创建/搜索/反馈/版本历史 |
| 技能进化 | 2 | 三级进化/L1→L2→L3→Skills |
| Hermes集成 | 3 | MCP Bridge/Memory Provider/资源生命周期 |
| 模型能力 | 2 | 模型路由梯队(4级)/跨模型兼容 |
| 记忆写入扩展 | 2 | 冲突合并策略/WM 沙箱验证环 |
| 校准与治理 | 6 | 宪法解释/监督平面/支持结构守护 |

---

## 五、文档体系 · Documentation（52 份）

| 分类 | 文档 |
|:-----|:------|
| **📐 foundation** | 架构设计 / 认知基础 / 设计理念 / 声明-实现映射 |
| **📋 specification** | API规格 / 数据模型 / 功能清单(99项) / 实现映射 / 操作目录(50项) / 追缴清单 / 需求 / NFR / 详细设计 |
| **🔧 development** | 技术栈 / 环境搭建 / 编码规范 / 集成设计 |
| **🏛 governance** | 架构决策 / 债务路线图 / 风险 / 项目计划 / 变更日志 / 发布流程 / 文档治理 |
| **⚙️ ops** | 部署 / 配置(60+参数) / 可靠性 / 可观测性 / 故障排查 / 运维手册 |
| **✅ quality** | 测试策略 / 验收标准 / 基准计划 / 测试计划 |
| **🔒 security** | 威胁模型(S-01~S-19) / 安全规格 |
| **📖 user** | 快速入门 / 用户指南 |
| **📚 references** | 术语表 / 错误参考 / 可追溯性映射 / 算法文档 |
| **📝 reviews** | 审计报告 / 评审文档 |

---

## 六、技术栈 · Technology Stack

| 层 | 技术选型 | 
|:----|:---------|
| 运行时 | Python 3.11+ / Litestar |
| 数据库 | PostgreSQL 16 + pgvector |
| 轻量存储 | SQLite（本地模式）|
| 知识图谱 | PostgreSQL 递归 CTE / Apache AGE（评估中）|
| 向量 | pgvector HNSW / SQLite-vec |
| MCP | Model Context Protocol 原生集成 |
| 检索 | 6维混合排序 + BM25 FTS5 + Cross-encoder |
| 推断 | 本地轻量模型 + 云端 LLM 混合路由 |
| 部署 | Docker compose / Dockerfile |

---

## 七、开发状态 · Development Status

| 阶段 | 状态 |
|:-----|:-----|
| 🏗 文档底座 | ✅ **已完成** — 52 份文档，99 项能力规格就绪 |
| 🎯 架构冻结 | ✅ **已完成** — 设计决策全部收敛，已知债务分类在册 |
| 📝 系统设计 | ✅ **已完成** — 数据模型/API规格/实现映射/操作目录就绪 |
| 💻 代码实现 | ⬜ **未启动** — 代码仓库为空，待文档审核定稿后启动 |

---

## 八、快速链接 · Quick Links

| 目标 | 路径 |
|:-----|:------|
| **系统架构（核心规格）** | [`docs/foundation/architecture-v1.0.0.md`](docs/foundation/architecture-v1.0.0.md) |
| **认知基础** | [`docs/foundation/cognitive-foundation.md`](docs/foundation/cognitive-foundation.md) |
| **功能清单（99 项）** | [`docs/specification/feature-list.md`](docs/specification/feature-list.md) |
| **数据模型** | [`docs/specification/data-model.md`](docs/specification/data-model.md) |
| **API 规格** | [`docs/specification/api-spec.md`](docs/specification/api-spec.md) |
| **操作目录（50 项）** | [`docs/specification/operation-catalog.md`](docs/specification/operation-catalog.md) |
| **待实现债务** | [`docs/governance/debt-collection.md`](docs/governance/debt-collection.md) |
| **部署指南** | [`docs/ops/deployment.md`](docs/ops/deployment.md) |
| **配置参数** | [`docs/ops/configuration.md`](docs/ops/configuration.md) |
| **文档索引** | [`docs/README.md`](docs/README.md) |

---

## License

MIT — see [LICENSE](LICENSE)
