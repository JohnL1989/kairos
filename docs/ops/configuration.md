---
title: Kairos 配置参数参考
aliases:
  - 配置参数
  - configuration-parameters
tags:
  - kairos
  - ops
  - configuration
created: 2026-07-18
updated: 2026-07-20
status: v1.0.0
---

# Kairos 配置参数参考

> **文档定位：** 架构文档中声明为「可配置」的默认参数值汇总。本文所有默认值可随部署环境调整，调整不违反架构级不变量或安全红线。

---

## 一、架构层参数（按章节）

### §1 宪法主权面

| 参数 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `EXPLANATION_EXHAUSTION_ALERT_THRESHOLD` | 3 次 | 解释枯竭告警连续触发此次数后申请推理悬挂 |
| `VIRTUAL_CALIBRATION_CONFIDENCE_CAP` | 0.6 | 虚拟校准信号的置信度上限 |
| `VIRTUAL_CALIBRATION_SIMILARITY_THRESHOLD` | 0.7 | 虚拟校准与见证锚定比对的相似度阈值 |
| `VIRTUAL_CALIBRATION_CONFLICT_THRESHOLD` | 3 次 | 连续冲突次数超过此值触发拟真校准失稳告警 |

### §2 元认知层

| 参数 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `BLIND_SPOT_PROXIMITY_RADIUS` | 0.3（余弦距离） | 盲区标注「几何邻近」的半径 |
| `BLIND_SPOT_SEMANTIC_DIVERGENCE_THRESHOLD` | 0.6（余弦距离） | 盲区标注「语义迥异」的阈值 |
| `EMOTIONAL_VAD_DEVIATION_SIGMA` | 1.5σ | 情感 VAD 偏移背离标准差倍数，超过此值情感提升权重衰减至零 |
| `META_AUDIT_ENTROPY_SURGE_THRESHOLD` | 3× 基线标准差 | 决策熵异常飙升的判定阈值（相对于基线偏差倍数） |
| `META_AUDIT_ENTROPY_MEASUREMENT_WINDOW` | 10 个调度周期 | 决策熵测量的滑动窗口长度 |
| `HEALTH_MONITOR_PERIOD` | 5 个调度周期 | 健康计数器连续无异常的判定周期数 |
| `HEALTH_MONITOR_LATENCY_THRESHOLD` | 500ms | 环延迟告警阈值 |
| `FROZEN_EMERGENCY_TIMEOUT` | 30 个调度周期 | 应急冻结自动进入安全降级持久态的超时 |
| `FROZEN_COOLDOWN_PERIOD` | 3 个调度周期 | 冻结解除后不接受探索投资的冷启动期 |

### §3 策略层

| 参数 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `PREDICTOR_ATTRIBUTION_TTL` | 3 个调度周期 | 任务归档后使用权重冻结前的窗口 |
| `COMPOSITION_RETRIEVAL_WEIGHT` | 1.2 | 检索级负载系数 |
| `COMPOSITION_SIMULATION_WEIGHT` | 1.8 | 模拟级负载系数 |
| `COMPOSITION_VERIFICATION_WEIGHT` | 1.4 | 验证级负载系数 |
| `COMPOSITION_CONTRIBUTION_WEIGHT` | 1.6 | 贡献级负载系数 |
| `COMPOSITION_IMPLICIT_WEIGHT` | 2.0 | 内隐级负载系数 |
| `CONSTITUTIONAL_LOCK_PERIOD` | 1000 个外部校准周期 | 辞典式排序优先级链的最小锁定周期 |
| `EDGE_SLOT_TIMEOUT_MULTIPLIER` | 3× | 边缘槽超时倍数 |
| `SANDBOX_CONFIDENCE_INTEGRATION_THRESHOLD` | 0.7 | 沙箱验证环允许合并的置信度积分阈值（属 WM 层，见 §5） |
|
### §4 存储层

| 参数 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `LATENT_REVIVAL_MATCH_THRESHOLD` | 0.65（余弦相似度） | 潜伏记忆二级匹配的相似度阈值 |
| `LATENT_REVIVAL_INITIAL_CONFIDENCE` | 80% | 复兴加速通道的影子副本置信度初始值（占积累阈值比例） |
| `FORGETTING_SCORE_THRESHOLD` | 0.75 | 遗忘调度器触发压缩/归档的遗忘得分阈值 |
| `WITNESS_UPDATE_BARRIER_N_DEFAULT` | 3 | 更新势垒 N 的默认值（外部校准可上调） |
| `NARRATIVE_COHERENCE_FALLBACK_SCORE` | 0.5 | 叙事自洽度评估器不可用时的默认分 |
| `INTEGRATION_CONSISTENCY_PERIOD` | 5 个调度周期 | 反向调整方向一致判定周期数 |
| `INTEGRATION_COOLDOWN_PERIOD` | 10 个调度周期 | 反向调整冷却期 |
| `EMOTIONAL_DE_AMPLIFICATION_RATIO` | 50% | 情感去强化时 arousal→更新势垒增益的衰减比例 |
| `EMOTIONAL_DE_AMPLIFICATION_WINDOW` | 20 个调度周期 | 情感去强化默认窗口长度 |
| `ENCODING_BUDGET_RATIO` | 3:3:2:2 | 情景:叙事:语义:程序的编码预算分配比例 |
| `CONFLICT_RESOLUTION_SIMILARITY_HIGH` | 0.9 | 补充/修正/重构判定的高相似度阈值 |
| `CONFLICT_RESOLUTION_SIMILARITY_MEDIUM` | 0.5 | 补充/修正/重构判定的中相似度阈值下限 |
| `COMPLEXITY_BUDGET_THRESHOLD` | 15 | 跨层协调协议复杂度阈值（层数 × 接口数） |
| `DEGRADATION_PERIOD_N` | 50 个调度周期 | 他律性降级契约——保守静默模式的阈值 |
| `DEGRADATION_PERIOD_M` | 200 个调度周期 | 他律性降级契约——受限内部验证模式的阈值 |
| `COGNITIVE_JOINT_BACKUP_PATH` | `~/.kairos/backups/cognitive-joints/` | 认知关节可逆执行的备份目录 |
| `OBSERVATION_WINDOW_PERIODS` | 5 个调度周期 | 认知关节调整后的双轨观察窗口长度 |
| `SANDBOX_TIMEOUT_PERIODS` | 90 | 沙箱验证环超时待定状态自动拒绝的周期数 |
| `INVARIANT_OBSERVATION_WINDOW_PERIODS` | 3 | 不变量修订门禁的观察窗口期长度 |
| `REVERSE_CHAIN_FEEDBACK_PERIODS` | 3 | 逆向链反馈升级观察周期数 |
| `SEED_ANCHOR_PATH_PREFIX` | `kairos://_system/seeds/` | 冷启动种子价值源的路径前缀 |
| `SEED_ANCHOR_MAX_ITEMS` | 10 | 种子锚点的最大条目数 |
| `HEALTH_MONITOR_RECOVERY_PERIODS` | 5 | 健康计数器自动撤销降级信号所需连续无异常周期数 |
| `HEALTH_MONITOR_TIMEOUT_PERIODS` | 30 | 健康计数器超时后升级为紧急冻结请求的周期数 |

### §5 工作记忆层（WM）

| 参数 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `WM_SLOT_CAPACITY` | 7±2 | WM 维护缓冲槽位上限（与注意力调度器资源池关联） |
| `WM_OPERATION_BUDGET` | 5 次/周期 | 每个调度周期内 WM 操作空间的最大推理/比较/组合操作次数 |
| `SANDBOX_CONFIDENCE_INTEGRATION_THRESHOLD` | 0.7 | 沙箱验证环允许合并的置信度积分阈值 |
| `SIMULATION_ISOLATION_TTL` | 3 个调度周期 | 模拟隔离区缓存项的超时时间 |
| `EXTRACTION_SUPPRESSION_INHIBITION_RATIO` | 0.7 | 提取抑制的多路径衰减加权系数 |
| `EPSILON_LAG_INJECTION_RATE` | 0.3 | ε滞后注入的默认滞后系数 |
| `CORTEX_DEGRADATION_TRIGGER_LATENCY` | 2000ms | 推理皮层退化的外部推理引擎延迟阈值（超过此值皮层不可退化） |

### §6 接入层

| 参数 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `PROVIDER_DEFAULT_ACCURACY` | 0.5 | 新 Provider 参与加权前的默认历史准确率 |
| `PROVIDER_MIN_CALIBRATION_EVENTS` | 5 | 新 Provider 参与加权所需的最小校准事件数 |

### §7 安全红线

| 参数 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `RATE_LIMIT_WRITE_PER_MIN` | 60 | 写操作限流（每分钟请求数） |
| `RATE_LIMIT_READ_PER_MIN` | 120 | 读操作限流（每分钟请求数） |
| `INPUT_LIMIT_CONTENT_BYTES` | 65536 | content 字段最大长度（字节，64KB 硬上限） |
| `INPUT_LIMIT_QUERY_CHARS` | 500 | query 字段最大字符数 |

### §8 质量属性

（本节参数见 §8.1 表）

### §8.1 见证→使用仲裁参数

| 参数 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `WITNESS_SURGE_WINDOW` | 10 个调度周期 | 陡升检测的单位时间窗口 |
| `WITNESS_SURGE_THRESHOLD` | 40% | 窗口内升幅超过此值触发差异检验 |
| `WITNESS_GRADUAL_PERIOD` | 30 个调度周期 | 渐进式上升连续周期数 |
| `WITNESS_DIFFERENCE_SIMILARITY_THRESHOLD` | 0.6（余弦相似度） | 语义内核相似度比对阈值，低于此值标记存疑 |
| `WITNESS_ALERT_PERIOD` | 3 个调度周期 | 检测器持续背离外部校准后发出告警 |

### §8.3 质量指标

| 指标 | 值 | 属性 |
|:-----|:---|:-----|
| 保守倾向平局率 | ≤ 5% | 上限（超过触发宪法解释层审视） |

---

## 二、运行时动态调整规则

架构中所有可配置参数支持两类调整模式：

| 模式 | 授权者 | 约束 |
|:-----|:-------|:-----|
| **运维静态配置** | 运维/部署者 | 通过环境变量或配置文件设定，重启生效 |
| **元认知层动态调参** | 元认知层治理器族 | 仅在宪法级约束范围内调整，且受元审计子层监测。每秒调参不超过 1 次 |
| **外部校准驱动调整** | 宪法主权面外部校准端口 | 可临时覆盖任意参数值，覆盖有效期随校准信号生命周期 |

**动态调参不变量（任何时候均不得违反）：**
1. 安全红线（S-01~S-16）阈值不可调低
2. 跨层三环不变量（§8.1）不可被调参破坏
3. 辞典式排序优先级链不受动态调参影响（受 CONSTITUTIONAL_LOCK_PERIOD 保护）

---

## 版本记录

| 版本 | 日期 | 变更 |
|:----|:----|:-----|
| v1.0.0 | 2026-07-18 | Kairos 配置参数参考。§1:4项，§2:9项，§3:9项，§4:24项，§5:7项，§6:2项，§7:4项，§8:0项，§4.3-4.4:5项 = 64 项参数。含运行时动态调整规则与不变量。 |
