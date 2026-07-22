---
title: Kairos 详细设计
aliases:
  - 组件设计
  - 详细设计
  - detailed-design
tags:
  - kairos
  - design
  - implementation
created: 2026-07-21
updated: 2026-07-21
status: draft
> **说明**：本文为施工图纸（设计稿），组件状态见下方索引表。待首迭代完成核心 3 组件后晋升为 v1.0.0。当前 status=draft，非发布版本。
---

# Kairos 详细设计

> **定位**：architecture-v1.0.0.md 是「鸟瞰图」，本文是「施工图纸」——每个核心组件的内部结构、状态机、核心算法伪代码、接口定义。代码启动后第一个迭代内完成核心 3 组件（WM 管理器 / 存储引擎 / 遗忘引擎），校准调度器与事件总线同为 P0 但归入第二迭代，其余随开发补齐。

---

## 组件索引

| 组件 | 章节 | 优先级 | 状态 |
|:-----|:----:|:-----:|:----:|
| WM 管理器 | §1 | P0 | 待实现 |
| 存储引擎 | §2 | P0 | 待实现 |
| 遗忘引擎 | §3 | P0 | 待实现 |
| 升华管道 | §4 | P1 | 待实现 |
| 校准调度器 | §5 | P0 | 待实现 |
| 元认知检测器 | §6 | P1 | 待实现 |
| 推理皮层 | §7 | P1 | 待实现 |
| 事件总线 | §8 | P0 | 待实现 |

---

## §1 WM 管理器

### 职责边界

- 维护当前活跃记忆槽位（7±2）
- 管理检索候选集（路径 + 语义 + 关系多路径融合，情感通过关系标签注入）
- 与注意力调度器协作（架构 §9，全局资源分配）
- 提供推理皮层子模块上下文

### 状态机

```
         ┌─────────────┐
         │   IDLE      │ ← 无待办任务，等待输入
         └──────┬──────┘
                │ 检索请求到达
                ▼
         ┌─────────────┐
    ┌─→  │ RETRIEVING  │ ← 多路径并行检索
    │    └──────┬──────┘
    │           │ 候选集到达
    │           ▼
    │    ┌─────────────┐
    │    │ FUSING      │ ← 多路径交叉筛选+融合
    │    └──────┬──────┘
    │           │ 融合完成
    │           ▼
    │    ┌─────────────┐
    │    │ OPERATING   │ ← 推理皮层操作结果
    │    └──────┬──────┘
    │           │ 操作完成 / 超时
    │           ▼
    │    ┌─────────────┐
    └────│  STABILIZING│ ← 再稳定化（检索后）
         └──────┬──────┘
                │ 稳定化完成
                ▼
              IDLE
```

### 核心接口

```python
class WMManager:
    async def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        """多路径检索→融合→返回"""
        ...

    async def operate(self, context: WMContext) -> Action:
        """推理皮层操作入口"""
        ...

    async def stabilize(self, memory_id: UUID):
        """检索后再稳定化"""
        ...
```

### 多路径融合算法（伪代码）

```
FUSE(candidates_by_path):
    # 交集 → 直接进 WM
    intersection = INTERSECT(candidates_by_path)
    
    # 独有 → 按信息增益筛选
    unique = UNION(candidates_by_path) - intersection
    filtered = []
    for candidate in unique:
        gain = INFORMATION_GAIN(candidate, intersection)
        if gain > GAIN_THRESHOLD:  # v1.0 默认 0.15，可由 KAIROS_FUSE_GAIN_THRESHOLD 配置
            filtered.append(candidate)
    
    # 提取抑制：高并发低互补路径衰减
    for path_a, path_b in PAIRS_WITH_HIGH_OVERLAP(candidates_by_path):
        if MUTUAL_INFORMATION_GAIN(path_a, path_b) < 0:
            DECAY_WEIGHT(path_b, SUPPRESSION_FACTOR)  # v1.0 默认 0.3，可由 KAIROS_FUSE_SUPPRESSION_FACTOR 配置
    
    return intersection + filtered
```

---

## §2 存储引擎

### 职责边界

- 统一 LTM 存储（SQLite / PostgreSQL 后端抽象）
- 双副本管理（见证锚定主副本 + 使用权重影子副本）
- 路径空间索引（`kairos://` 前缀树）
- 关系索引（边+类型）
- 情感效价空间（VAD 三维独立存储）

### 数据流：写入路径

```
写入请求
  │
  ▼
Access Layer → 验证门禁（高信用源豁免→跳过 raw）
  │
  ▼
写入 raw 层（不可检索）
  │
  ▼
摄取验证环 → 失败 → 丢弃
  │ 通过
  ▼
升格为 item（可检索）
  │
  ├──→ 写入见证锚定主副本（强一致）
  ├──→ 初始化使用权重影子副本（最终一致）
  ├──→ 注册路径空间（前缀树插入）
  ├──→ 建立关系索引（若有关系标注）
  └──→ 记录情感效价（若有 VAD）
```

### 后端抽象接口

```python
class StorageBackend(ABC):
    @abstractmethod
    async def write(self, memory: Memory) -> UUID: ...
    
    @abstractmethod
    async def path_retrieve(self, prefix: str) -> list[Memory]: ...
    
    @abstractmethod
    async def vector_search(self, query: list[float], top_k: int) -> list[ScoredMemory]: ...
    
    @abstractmethod
    async def update_witness(self, memory_id: UUID, witness: dict): ...
    
    @abstractmethod
    async def update_usage(self, memory_id: UUID, delta: UsageDelta): ...
```

---

## §3 遗忘引擎

### 职责边界

- 定时扫描遗忘候选（遗忘调度器）
- 计算遗忘得分（二维遗忘曲面 + 使用频率调制）
- 潜伏势能重估（盲区驱动 + 前向关联扫描）
- 复兴加速通道（遗忘后悔补偿）

### 遗忘得分算法（伪代码）

```
FORGETTING_SCORE(memory):
    # 基础分：二维遗忘曲面
    decontext = memory.age_days / DECONTEXT_HALF_LIFE
    age_factor = SIGMOID(memory.age_days / AGE_DECAY_CONSTANT)
    base_score = decontext * age_factor
    
    # 使用频率调制
    recent_use = memory.usage_count_last_30d
    frequency_mod = 1.0 / (1.0 + LOG(1 + recent_use))
    
    # 契约类型系数
    contract_mod = {
        "permanent": 0.0,     # 常驻：不遗忘
        "ondemand": 1.0,      # 按需：标准
        "environmental": 1.5, # 环境：更易遗忘
        "temporary": 2.0,     # 临时：最快遗忘
    }[memory.contract]
    
    # 身份与结构豁免
    if memory.is_identity or memory.is_structure:
        return 0.0
    
    score = base_score * frequency_mod * contract_mod
    return CLAMP(score, 0.0, 1.0)
```

### 遗忘调度器状态机

```
          ┌──────────────┐
          │   SCHEDULING  │ ← 等待调度周期
          └──────┬───────┘
                 │ 周期到达
                 ▼
          ┌──────────────┐
          │   SCANNING    │ ← 遍历记忆计算遗忘得分
          └──────┬───────┘
                 │ 得分 > 阈值
                 ▼
          ┌──────────────┐
          │   CANDIDATING │ ← 标记为遗忘候选（非立即删除）
          └──────┬───────┘
                 │ 候选期结束 + 无复兴命中
                 ▼
          ┌──────────────┐
          │   EVICTING    │ ← 从主存储移除
          └──────┬───────┘
                 │ 移除完成
                 ▼
              SCHEDULING
```

---

## §4 升华管道

### 触发条件

- 系统空闲（无待办任务、无检索请求）→ 自动触发
- 用户手动触发特定路径 `kairos sublimation trigger --path kairos://...`

### 四阶段流程

```
raw（原始表征，不可检索）
  │
  │  验证通过（摄取门禁）
  ▼
item（标准表征，可检索）
  │
  │  空闲周期离线重组
  │  └─ 回放：稳定化不稳定记忆
  │  └─ 抽象萃取：从多条 item 提取模式 → strategy
  ▼
strategy（抽象模式，跨场景适用）
  │
  │  行为固化
  │  └─ 人工确认门控（必须确认，默认开——模拟产物未经实证不得转正，违反 S-13）
  ▼
behavior（自动化行为规则，不检索直接输出）
```

---

## §5 校准调度器

### 职责

- 接收外部校准信号（REST 端点 / CLI）
- 与见证锚定主副本比对（差异检验）
- 更新见证锚定或触发降级

### 核心循环（伪代码）

```
CALIBRATION_LOOP:
    while True:
        signal = AWAIT_CALIBRATION_SIGNAL(timeout=DEFAULT_TIMEOUT)  # v1.0 默认 300s（见 KAIROS_CALIBRATION_TIMEOUT）
        
        if signal is None:  # 超时静默
            IDLE_COUNTER++
            if IDLE_COUNTER > CALIBRATION_SILENT_THRESHOLD:  # v1.0 默认 6 次超时（见 KAIROS_CALIBRATION_SILENT_COUNT）
                GENERATE_VIRTUAL_CALIBRATION()
            continue
        
        IDLE_COUNTER = 0
        
        # 差异检验
        diff = COMPUTE_DIFF(signal, witness_anchor)
        
        if diff < MERGE_THRESHOLD:  # v1.0 默认 0.15（cosine 距离），见 KAIROS_CALIBRATION_MERGE_THRESHOLD
            # 一致：合并
            MERGE_INTO_WITNESS(signal)
        elif diff < CONFLICT_THRESHOLD:  # v1.0 默认 0.35（cosine 距离），见 KAIROS_CALIBRATION_CONFLICT_THRESHOLD
            # 轻微偏差：加权融合
            WEIGHTED_MERGE(signal, CONFIDENCE(signal))
        else:
            # 冲突：进入冲突消解协议
            RESOLVE_CONFLICT(signal)
        
        # 审计记录
        AUDIT_LOG("calibration", signal_id=signal.id, diff=diff)
```

---

## §6 元认知检测器（概要）

| 检测器 | 监测指标 | 输出 |
|:-------|:---------|:-----|
| 情感流形监测器 | VAD 空间中记忆簇的激活预算占比 | 情感去强化触发信号 |
| 盲区覆盖率监测器 | 向量空间低密度区域占比 | 探索预算调整信号 |
| 叙事连贯性检测器 | 叙事自洽度时间序列趋势 | 身份漂移告警 |
| VAD 独立性测试器 | VAD 值是否可由其他轴完全预测 | 证伪信号 |
| 耦合计监测器 | 四轴之间的相关性趋势 | 轴正交假设证伪信号 |
| 偏置监测器 | 心境一致性/确认偏误积累 | 偏置告警 |

---

## §7 推理皮层（概要）

架构详见 `architecture-v1.0.0.md §4`（推理皮层）。核心循环：

### 层级蒸馏管道

五层时间记忆树的蒸馏循环：

```
LAYER_DISTILL(session_id):
    # L0: 写入原始轮次
    journal_entries ← (session_id, role, content, source, platform)
    
    # L1: 会话摘要（session 结束时触发）
    rows ← SELECT * FROM journal_entries WHERE session_id = $1
    summary ← LLM("将以下对话提炼为会话摘要", rows)  # 或启发式摘要
    key_decisions ← LLM("提取关键决策", rows)
    entities ← extract_entities(rows)  # 实体提取
    INSERT INTO session_summaries (session_id, summary, key_decisions, entities)
    
    # L2: 日报告（日终触发）
    sessions ← SELECT * FROM session_summaries WHERE date = today
    daily_summary ← LLM("聚合以下会话摘要为日报告", sessions)
    INSERT INTO daily_reports (report_date, summary, insights, session_count)
    
    # L3: 周知识包（周终触发）
    dailies ← SELECT * FROM daily_reports WHERE week = current_week
    patterns ← LLM("分析以下日报告的重复模式", dailies)
    INSERT INTO weekly_packs (week_start, patterns, trends, key_decisions)
    
    # L4: 画像更新（持续触发，增量）
    profile ← SELECT * FROM user_profiles WHERE user_id = $1
    new_prefs ← extract_preferences(sessions, dailies)
    profile.preferences ← merge(profile.preferences, new_prefs)
    UPDATE user_profiles SET preferences = $1, version = version + 1
```

蒸馏置信度低于 KAIROS_CAPTURE_CONFIDENCE_FLOOR（默认 0.6）的产物标记为待审，
不自动进入上层。关系检测在 L1 阶段执行。
REASONING_LOOP(context):
    # 1. 向预测器查询预激活集
    pre_activated = PREDICTOR.QUERY(context)
    
    # 2. 候选集上下文裁剪
    candidates = CORTEX.FILTER(pre_activated, context)
    
    # 3. 推理输出行动决策
    action = CORTEX.REASON(candidates, context)
    
    # 4. 执行后更新使用事件
    EVENT_BUS.EMIT("use_event", candidates)
    
    return action
```

---

## §8 事件总线

### 事件格式

```json
{
  "event_id": "uuid",
  "event_type": "calibration_signal | degradation_switch | use_event | intention_activate | intention_resolve | affective_boost | exploration_budget | latent_trigger | attention_allocation | sublimation_tick",
  "source": "storage_layer | strategy_layer | wm_layer | metacognition_layer | sovereignty_plane",
  "priority": 0,
  "payload": {},
  "timestamp": "ISO 8601"
}
```

### 事件类型表

> 事件定义以 `api-spec.md` §四为权威来源，完整枚举见 `architecture-v1.0.0.md §10.10`。本文仅引用，不新增事件类型。

| event_type | 发送者 | 接收者 | 说明 |
|-----------|:-------|:-------|:-----|
| `use_event` | WM | 策略+存储+元认知 | 使用事件提交 |
| `calibration_signal` | 宪法主权面 | 全层广播 | 外部校准信号注入 |
| `degradation_switch` | 宪法主权面 | 全层广播 | 降级模式切换 |
| `intention_activate` | 策略层 | WM | 前瞻意图激活 |
| `intention_resolve` | WM | 策略→存储 | 前瞻意图完成/取消 |
| `affective_boost` | 策略层 | WM | 情感基线提升注入 |
| `exploration_budget` | 元认知层 | 策略层 | 探索预算分配 |
| `latent_trigger` | 元认知层 | 存储层 | 潜伏势能重估触发 |
| `attention_allocation` | 注意力调度器 | 元认知层 | 注意力分配日志 |
| `sublimation_tick` | 存储层 | 自身 | 升华管道轮次推进 |

---

## 版本记录

| 版本 | 日期 | 变更 |
|:----|:----|:-----|
| v1.0.0 | 2026-07-21 | 初始版本。WM/存储/遗忘三核心组件 + 升华/校准/元认知/皮层/事件总线概要。本文为 draft，非发布版本。 |
