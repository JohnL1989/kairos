---
title: Kairos 架构实现映射
aliases:
  - 实现映射
  - Implementation Map
tags:
  - kairos
  - design
  - implementation
created: 2026-07-20
updated: 2026-07-20
status: draft
---

# Kairos 架构实现映射

> **定位**：将架构设计文档中的每一组件映射到 `src/` 下的具体模块路径。编码启动后，开发者可据此快速定位对应实现。

**引用约定：** `架构 §X.Y` 指 `foundation/architecture-v1.0.0.md` 第 X 节第 Y 小节。架构文档含 §0–§12（含 §10 质量属性与不变量等）。代码路径以 `src/` 为根。

---

## 一、宪法主权面 §1

| 架构组件 | 代码路径 | 说明 |
|:--------|:---------|:-----|
| 外部校准端口 | `src/sovereignty/calibration.py` | 接收外部校准信令（REST/CLI），鉴权后写入见证锚定 |
| 宪法修订端口 | `src/sovereignty/constitution.py` | 宪法级偏好查看与修订（需 admin Key） |
| 强制冻结机制 | `src/sovereignty/freeze.py` | 冻结/解冻所有内部环，到期自动解冻 |
| 虚拟校准生成器 | `src/sovereignty/virtual_calibration.py` | 外部静默时生成拟真校准，置信度上限锁定 |
| 宪法解释层 | `src/sovereignty/interpretation.py` | 抽象原则→语境判例映射，判例置信度衰减 |
| 降级状态机 | `src/sovereignty/degradation.py` | 三模式切换（保守静默/受限交叉验证/安全休眠） |

## 二、元认知层 §2

| 架构组件 | 代码路径 | 说明 |
|:--------|:---------|:-----|
| 检测器族 | `src/metacognition/detectors/` | 各类监测器（流形曲率/分布偏移/情感流形/偏置等） |
| 元记忆偏置监测器 | `src/metacognition/detectors/bias.py` | 跟踪熟知感/盲区感知/校准感三维度 |
| 健康计数器 | `src/metacognition/health_counter.py` | 独立旁路，监测环延迟/死锁，唯一权限触发降级信号 |
| 自观察记忆 | `src/metacognition/self_observation.py` | 治理动作后效记录（只读镜像，不可再巩固） |
| 治理器族 | `src/metacognition/governors/` | 巩固门控、用途对齐审批等治理组件 |

## 三、策略层 §3

| 架构组件 | 代码路径 | 说明 |
|:--------|:---------|:-----|
| 预测器 | `src/strategy/predictor.py` | 基于路径空间的使用概率预测，组合寄存器 |
| 调节器 | `src/strategy/modulator.py` | 内隐偏向注入 + 探索投资（动态δ） |
| 价值上下文管理器 | `src/strategy/value_context.py` | 帕累托约束集 + 保守倾向闸门 + 辞典式裁决器 |
| 路径注册表 | `src/strategy/path_registry.py` | 每类记忆的检索路径深度度量 |

## 四、存储层 §4（存储核心 → 记忆生命周期 → 关系与图谱 → 维护）

| 架构组件 | 代码路径 | 说明 |
|:--------|:---------|:-----|
| 数据模型定义 | `src/storage/models.py` | 19 张表（11 核心 + 8 张 v1.0 新增）ORM 定义（memories/relations/usage 等） |
| 记忆 CRUD | `src/storage/memory_store.py` | 记忆写入/检索/更新/导出/删除 |
| 路径空间索引 | `src/storage/path_index.py` | `kairos://` 路径前缀索引与树状查询 |
| 向量索引 | `src/storage/vector_index.py` | pgvector/sqlite-vec 语义相似度搜索 |
| 关系索引 | `src/storage/relation_index.py` | 四类关系 + 粒度关系的 CRUD 与查询 |
| 双副本管理 | `src/storage/dual_copy.py` | 见证锚定（强一致）与使用权重（最终一致）分离管理 |
| 升华管道 | `src/storage/sublimation_pipeline.py` | raw→item→strategy→behavior 四阶段状态机，含 L0-L4 层级蒸馏 |
| 遗忘调度器 | `src/storage/forgetting.py` | 二维遗忘曲面计算 + 潜伏势能重估 + 复兴加速 |
| 后台维护引擎 | `src/storage/maintenance.py` | Light/Deep 双模定时维护（热度衰减/冗余合并/实体提取/TMT补扫/P6合规） |
| 主动话题生成器 | `src/storage/proactive_topic.py` | Deep 模式驱动，4 种信号源生成 proactive topics |
| 实体知识图谱 | `src/storage/entity_graph.py` | entities + memory_entities 表管理，递归 CTE 多跳遍历 |
| 对话历史持久化 | `src/storage/conversation.py` | conversation_messages 表管理，同步/分页查询 |
| 长文本分块引擎 | `src/storage/chunking.py` | 200-600 字重叠窗口分块，异步写入分块队列 |
| 冲突检测 | `src/storage/conflict_detection.py` | 语义相似度 + 文本 diff 双重冲突/重复检测 |
| 模型路由 | `src/storage/model_routing.py` | 4 级梯队 + 自动升降级 + 双层语义缓存 |
| 知识加工区门闸 | `src/storage/hall_gate.py` | 三区域写入 / 推进 / 退回状态机 + 闸机校验 |
| 端云同步 | `src/storage/sync.py` | SQLite ↔ PostgreSQL 增量双向同步 + 快照导入导出 |
| 记忆状态机 | `src/storage/memory_state_machine.py` | Active→Stale→Archived→Superseded 四态 + 状态变更跟踪 |
| 知识演化追踪 | `src/storage/knowledge_evolution.py` | Jaccard+语义 4 类演化关系检测 + 演化链查询 |
| RL 权重优化器 | `src/storage/rl_optimizer.py` | Cosine LR + ε-greedy + RCW + KPop + EMA 权重优化 |
| 过程知识 Playbook | `src/storage/playbook.py` | 结构化 playbook 生命周期 + FTS 检索 + 反馈循环 |
| 三级技能进化 | `src/storage/skill_evolution.py` | L1→L2→L3→Skills 进化状态机 + world_model_rules |
| 事实新鲜度 | `src/storage/fact_freshness.py` | fact_freshness 表管理 + 过期扫描 + penalty 系数 |
| 社区检测 | `src/storage/community_detection.py` | Label Propagation/Leiden 社区聚类 + entity_communities 表 |

## 五、工作记忆层 §5

| 架构组件 | 代码路径 | 说明 |
|:--------|:---------|:-----|
| WM 核心 | `src/wm/core.py` | 维护槽位（7±2）、注意力分配、置换策略 |
| 模拟隔离区 | `src/wm/simulation.py` | 反事实假设空间的标记隔离 |
| 纠正检测器 | `src/wm/correction_detector.py` | 用户输入否定/改写/隐式纠正检测，注入差异检验 |
| 跨平台身份映射 | `src/access/identity_mapper.py` | KAIROS_USER_ALIASES 解析 + agent_id→canonical_user_id 映射 |
| 沙箱验证环 | `src/wm/sandbox.py` | 新类型试运行→元审计确认→合并 |
| 推理皮层 | `src/wm/reasoning_cortex.py` | 最小推理内核：前瞻监控/事件排序/候选裁剪 |
| 多路径融合 | `src/wm/multi_path.py` | 多路径结果集汇聚（交集/缓冲池/信息增益门槛） |
| ε 滞后注入 | `src/wm/epsilon_lag.py` | 外部任务效用系数，滞后更新切断自激循环 |

## 六、接入层 §6

| 架构组件 | 代码路径 | 说明 |
|:--------|:---------|:-----|
| REST API 路由 | `src/access/api/` | Litestar handler，约 20+ 端点 |
| CLI 命令 | `src/access/cli.py` | 27 条 CLI 命令 |
| MCP Bridge | `src/access/mcp/bridge.py` | MCP 服务器进程，10 tools（见 api-spec §6.9） |
| Memory Provider | `src/access/provider/kairos_provider.py` | Hermes 原生记忆 Provider，6 lifecycle hooks |
| Agent Tool 定义 | `src/access/tools.py` | 4 个 Agent Tool（memories_write/memories_search/path_browse/memories_list_recent） |
| 干扰控制层 | `src/access/interference.py` | WM 负载超限时降级检索结果 |
| 鉴权中间件 | `src/access/auth.py` | API Key（read/write/admin 三级）鉴权 |
| 摄取验证门禁 | `src/access/ingestion.py` | 内容长度/路径格式/敏感信息/安全红线验证 |

## 七、监督平面 §7

| 架构组件 | 代码路径 | 说明 |
|:--------|:---------|:-----|
| 审计庭 | `src/supervision/audit_tribunal.py` | 审计日志记录 + HMAC 链维护 |
| 证伪响应路由器 | `src/supervision/falsification.py` | 耦合计监测/VAD 独立性测试/聚合审计信号路由 |
| 监督平面降级协议 | `src/supervision/degradation_protocol.py` | 监督平面自身的降级行为 |

## 八、横切组件 Cross-cutting

| 架构组件 | 代码路径 | 说明 |
|:--------|:---------|:-----|
| 事件总线 | `src/events/bus.py` | 事件发布/订阅/背压，基于 usage_events 表 |
| 事件类型定义 | `src/events/types.py` | 10 类事件枚举 + 消息结构 |
| 配置加载 | `src/config.py` | 环境变量/配置文件加载，70 项参数 |
| CLI 入口 | `src/main.py` | 应用入口点（Click/Typer CLI 框架） |
| 调度器 | `src/scheduler.py` | 升华/遗忘/重估等周期性任务调度（APScheduler） |
| 工具函数 | `src/utils/` | 通用工具（嵌入/Hash/脱敏/日志等） |

---

## 九、测试映射

| 测试类型 | 路径 | 目标 |
|:--------|:-----|:-----|
| 单元测试 | `tests/unit/` | 各层核心逻辑 + 19 条安全红线 |
| 集成测试 | `tests/integration/` | 接口契约 + 跨层交互 + 存储层 CRUD |
| E2E 测试 | `tests/e2e/` | 6 条关键用户路径 |

---

## 版本记录

| 版本 | 日期 | 变更 |
|:----|:----|:-----|
| v1.0.0 | 2026-07-20 | 初始实现映射。六层架构 + 横切 + 测试，约 80 个组件映射到 src/ 模块路径。 |
