---
title: Kairos 配置参数参考
aliases:
  - 配置文档
  - Configuration
tags:
  - kairos
  - ops
  - configuration
created: 2026-07-18
updated: 2026-07-22
status: draft
---

# Kairos 配置参数

> **时间单位定义**：本文中「个调度周期」为相对时间单位，1 调度周期 = `KAIROS_SCHEDULER_INTERVAL` 配置值（默认 300 秒 / 5 分钟）。所有以「调度周期」为单位的参数均以此值为基准换算。

> **参数名约定**：所有配置参数通过环境变量或配置文件设置，统一使用 `KAIROS_` 前缀。本文列出核心参数（v1.0 设计阶段的参数主索引）。部署模式特有参数（如 deployment.md 中的 `KAIROS_DB_DSN`、`KAIROS_LITE_MODE`）和可靠性参数（如 LLM 超时/熔断阈值）分别在对应文档中定义——本文为参数索引入口而非完整枚举。

> **状态声明**：以下参数为草稿完善阶段的设计值。框架实现版本锁定后可能微调。

## 一、架构层参数（按章节）

### §1 宪法主权面

| 参数 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `KAIROS_EXPLANATION_EXHAUSTION_ALERT_THRESHOLD` | 3 次 | 解释枯竭告警连续触发此次数后申请推理悬挂 |
| `KAIROS_VIRTUAL_CALIBRATION_CONFIDENCE_CAP` | 0.3 | 虚拟校准信号的置信度上限（架构定义：预设上限 0.3 且不可用于修宪） |
| `KAIROS_VIRTUAL_CALIBRATION_TIMEOUT` | 900 | 外部校准端口静默超过此时长（秒）后生成虚拟校准信号 |
| `KAIROS_VIRTUAL_CALIBRATION_SIMILARITY_THRESHOLD` | 0.7 | 虚拟校准与见证锚定比对的相似度阈值 |
| `KAIROS_VIRTUAL_CALIBRATION_CONFLICT_THRESHOLD` | 3 次 | 连续冲突次数超过此值触发拟真校准失稳告警 |

### §2 元认知层

| 参数 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `KAIROS_BLIND_SPOT_PROXIMITY_RADIUS` | 0.3（余弦距离） | 盲区标注「几何邻近」的半径 |
| `KAIROS_BLIND_SPOT_SEMANTIC_DIVERGENCE_THRESHOLD` | 0.6（余弦距离） | 盲区标注「语义迥异」的阈值 |
| `KAIROS_EMOTIONAL_VAD_DEVIATION_SIGMA` | 1.5σ | 情感 VAD 偏移背离标准差倍数，超过此值情感提升权重衰减至零 |
| `KAIROS_META_AUDIT_ENTROPY_SURGE_THRESHOLD` | 3× 基线标准差 | 决策熵异常飙升的判定阈值（相对于基线偏差倍数） |
| `KAIROS_META_AUDIT_ENTROPY_MEASUREMENT_WINDOW` | 10 个调度周期 | 决策熵测量的滑动窗口长度 |
| `KAIROS_HEALTH_MONITOR_PERIOD` | 5 个调度周期 | 健康计数器连续无异常的判定周期数 |
| `KAIROS_HEALTH_MONITOR_LATENCY_THRESHOLD` | 500ms | 环延迟告警阈值 |
| `KAIROS_FROZEN_EMERGENCY_TIMEOUT` | 30 个调度周期 | 应急冻结自动进入安全降级持久态的超时 |
| `KAIROS_FROZEN_COOLDOWN_PERIOD` | 3 个调度周期 | 冻结解除后不接受探索投资的冷启动期 |

### §3 策略层

| 参数 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `KAIROS_PREDICTOR_ATTRIBUTION_TTL` | 3 个调度周期 | 任务归档后使用权重冻结前的窗口 |
| `KAIROS_COMPOSITION_RETRIEVAL_WEIGHT` | 1.2 | 检索级负载系数 |
| `KAIROS_COMPOSITION_SIMULATION_WEIGHT` | 1.8 | 模拟级负载系数 |
| `KAIROS_COMPOSITION_VERIFICATION_WEIGHT` | 1.4 | 验证级负载系数 |
| `KAIROS_COMPOSITION_CONTRIBUTION_WEIGHT` | 1.6 | 贡献级负载系数 |
| `KAIROS_COMPOSITION_IMPLICIT_WEIGHT` | 2.0 | 内隐级负载系数 |
| `KAIROS_CONSTITUTIONAL_LOCK_PERIOD` | 1000 个外部校准周期 | 辞典式排序优先级链的最小锁定周期 |
| `KAIROS_EDGE_SLOT_TIMEOUT_MULTIPLIER` | 3× | 边缘槽超时倍数 |
| `KAIROS_SANDBOX_CONFIDENCE_INTEGRATION_THRESHOLD` | 0.7 | 沙箱验证环允许合并的置信度积分阈值（属 WM 层，见 §5） |
|
### §4 存储层

| 参数 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `KAIROS_LATENT_REVIVAL_MATCH_THRESHOLD` | 0.65（余弦相似度） | 潜伏记忆二级匹配的相似度阈值 |
| `KAIROS_LATENT_REVIVAL_INITIAL_CONFIDENCE` | 80% | 复兴加速通道的影子副本置信度初始值（占积累阈值比例） |
| `KAIROS_FORGETTING_SCORE_THRESHOLD` | 0.75 | 遗忘调度器触发压缩/归档的遗忘得分阈值 |
| `KAIROS_WITNESS_UPDATE_BARRIER_N_DEFAULT` | 3 | 更新势垒 N 的默认值（外部校准可上调） |
| `KAIROS_NARRATIVE_COHERENCE_FALLBACK_SCORE` | 0.5 | 叙事自洽度评估器不可用时的默认分 |
| `KAIROS_INTEGRATION_CONSISTENCY_PERIOD` | 5 个调度周期 | 反向调整方向一致判定周期数 |
| `KAIROS_INTEGRATION_COOLDOWN_PERIOD` | 10 个调度周期 | 反向调整冷却期 |
| `KAIROS_EMOTIONAL_DE_AMPLIFICATION_RATIO` | 50% | 情感去强化时 arousal→更新势垒增益的衰减比例 |
| `KAIROS_EMOTIONAL_DE_AMPLIFICATION_WINDOW` | 20 个调度周期 | 情感去强化默认窗口长度 |
| `KAIROS_ENCODING_BUDGET_RATIO` | 3:3:2:2 | 情景:叙事:语义:程序的编码预算分配比例 |
| `KAIROS_CONFLICT_RESOLUTION_SIMILARITY_HIGH` | 0.9 | 补充/修正/重构判定的高相似度阈值 |
| `KAIROS_CONFLICT_RESOLUTION_SIMILARITY_MEDIUM` | 0.5 | 补充/修正/重构判定的中相似度阈值下限 |
| `KAIROS_COMPLEXITY_BUDGET_THRESHOLD` | 15 | 跨层协调协议复杂度阈值（层数 × 接口数） |
| `KAIROS_DEGRADATION_PERIOD_N` | 50 个调度周期 | 他律性降级契约——保守静默模式的阈值 |
| `KAIROS_DEGRADATION_PERIOD_M` | 200 个调度周期 | 他律性降级契约——受限内部验证模式的阈值 |
| `KAIROS_COGNITIVE_JOINT_BACKUP_PATH` | `~/.kairos/backups/cognitive-joints/` | 认知关节可逆执行的备份目录 |
| `KAIROS_OBSERVATION_WINDOW_PERIODS` | 5 个调度周期 | 认知关节调整后的双轨观察窗口长度 |
| `KAIROS_SANDBOX_TIMEOUT_PERIODS` | 90 | 沙箱验证环超时待定状态自动拒绝的周期数 |
| `KAIROS_INVARIANT_OBSERVATION_WINDOW_PERIODS` | 3 | 不变量修订门禁的观察窗口期长度 |
| `KAIROS_REVERSE_CHAIN_FEEDBACK_PERIODS` | 3 | 逆向链反馈升级观察周期数 |
| `KAIROS_SEED_ANCHOR_PATH_PREFIX` | `kairos://_system/seeds/` | 冷启动种子价值源的路径前缀 |
| `KAIROS_SEED_ANCHOR_MAX_ITEMS` | 10 | 种子锚点的最大条目数 |
| `KAIROS_HEALTH_MONITOR_RECOVERY_PERIODS` | 5 | 健康计数器自动撤销降级信号所需连续无异常周期数 |
| `KAIROS_HEALTH_MONITOR_TIMEOUT_PERIODS` | 30 | 健康计数器超时后升级为紧急冻结请求的周期数 |

### §5 工作记忆层（WM）

| 参数 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `KAIROS_WM_SLOT_CAPACITY` | 7 | WM 维护缓冲槽位上限（与注意力调度器资源池关联） |
| `KAIROS_WM_OPERATION_BUDGET` | 5 次/周期 | 每个调度周期内 WM 操作空间的最大推理/比较/组合操作次数 |
| `KAIROS_SANDBOX_CONFIDENCE_INTEGRATION_THRESHOLD` | 0.7 | 沙箱验证环允许合并的置信度积分阈值 |
| `KAIROS_SIMULATION_ISOLATION_TTL` | 3 个调度周期 | 模拟隔离区缓存项的超时时间 |
| `KAIROS_EXTRACTION_SUPPRESSION_INHIBITION_RATIO` | 0.7 | 提取抑制的多路径衰减加权系数 |
| `KAIROS_EPSILON_LAG_INJECTION_RATE` | 0.3 | ε滞后注入的默认滞后系数 |
| `KAIROS_CORTEX_DEGRADATION_TRIGGER_LATENCY` | 2000ms | 推理皮层退化的外部推理引擎延迟阈值（超过此值皮层不可退化） |

### §6 接入层

| 参数 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `KAIROS_PROVIDER_DEFAULT_ACCURACY` | 0.5 | 新 Provider 参与加权前的默认历史准确率 |
| `KAIROS_PROVIDER_MIN_CALIBRATION_EVENTS` | 5 | 新 Provider 参与加权所需的最小校准事件数 |
| `KAIROS_DAILY_BUDGET_FEN` | 20000 | LLM 日预算上限（分，约 ¥200/天） |

### §7 安全红线

| 参数 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `KAIROS_RATE_LIMIT_WRITE_PER_MIN` | 60 | 写操作限流（每分钟请求数，单客户端级别）。系统容量 ≥100 ops/s（多客户端并行） |
| `KAIROS_RATE_LIMIT_READ_PER_MIN` | 120 | 读操作限流（每分钟请求数） |
| `KAIROS_INPUT_LIMIT_CONTENT_BYTES` | 65536 | content 字段最大长度（字节，64KB 硬上限） |
| `KAIROS_INPUT_LIMIT_QUERY_CHARS` | 500 | query 字段最大字符数 |
| `KAIROS_SSRF_ALLOWED_HOSTS` | `api.deepseek.com`（示例） | 出站 URL 白名单（逗号分隔）。部署时设为实际使用的 API 域名；`*`=无限制（不推荐生产） |
| `KAIROS_SSRF_IP_CHECK` | `true` | 解析 URL 后二次校验 IP，阻断内网/元数据地址 |
| `KAIROS_SSRF_DNS_REBIND_PROTECTION` | `true` | DNS 重绑定防护（DNS 解析结果与 HTTP 请求时的 IP 不一致时拒绝） |
| `KAIROS_WAL_ARCHIVE_COMMAND` | `cp %p ~/.kairos/wal_archive/%f` | PostgreSQL WAL 归档命令（`%p`=WAL 段路径，`%f`=文件名）。设为空字符串禁用归档 |
| `KAIROS_WAL_ARCHIVE_RETENTION_DAYS` | 7 | WAL 归档保留天数 |


### §8 质量属性

（本节参数见 §8.1 表）

### §8.1 见证→使用仲裁参数

| 参数 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `KAIROS_WITNESS_SURGE_WINDOW` | 10 个调度周期 | 陡升检测的单位时间窗口 |
| `KAIROS_WITNESS_SURGE_THRESHOLD` | 40% | 窗口内升幅超过此值触发差异检验 |
| `KAIROS_WITNESS_GRADUAL_PERIOD` | 30 个调度周期 | 渐进式上升连续周期数 |
| `KAIROS_WITNESS_DIFFERENCE_SIMILARITY_THRESHOLD` | 0.6（余弦相似度） | 语义内核相似度比对阈值，低于此值标记存疑 |
| `KAIROS_WITNESS_ALERT_PERIOD` | 3 个调度周期 | 检测器持续背离外部校准后发出告警 |

### §8.3 检索与蒸馏参数（v1.0 新增）

| 参数 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `KAIROS_RETRIEVAL_MIN_QUERY_LENGTH` | 3 | 检索触发最小 query 长度 |
| `KAIROS_RETRIEVAL_GREETING_PATTERNS` | "hi,hello,thanks,ok" | 问候/噪音模式列表 |
| `KAIROS_CAPTURE_MIN_LENGTH` | 10 | 捕获最小内容长度 |
| `KAIROS_CAPTURE_CONFIDENCE_FLOOR` | 0.6 | 蒸馏产物置信度下限 |
| `KAIROS_HEAT_DECAY_ALPHA` | 0.95 | 热度每日衰减系数 |
| `KAIROS_HEAT_ACCESS_BOOST` | 0.05 | 每次访问热度增量 |
| `KAIROS_SEARCH_WEIGHT_VECTOR` | 0.40 | 混合排序向量权重 |
| `KAIROS_SEARCH_WEIGHT_BM25` | 0.20 | 混合排序 BM25 权重 |
| `KAIROS_SEARCH_WEIGHT_TIME` | 0.15 | 混合排序时间权重 |
| `KAIROS_SEARCH_WEIGHT_RELIABILITY` | 0.10 | 混合排序可信度权重 |
| `KAIROS_SEARCH_WEIGHT_HEAT` | 0.15 | 混合排序热度权重 |

### §8.4 身份映射参数（v1.0 新增）

`KAIROS_IDENTITY_MAP` 为 JSON 格式，配置多平台用户 ID 到规范用户 ID 的映射：

```json
{
  "cross_platform_shared_scope": true,
  "user_aliases": {
    "telegram:user_123": "canonical_user_123",
    "cli:local": "canonical_user_123"
  }
}
```

仅在 `kairos://_user/` 域下生效。

### §8.5 质量指标

| 指标 | 值 | 属性 |
|:-----|:---|:-----|
| 保守倾向平局率 | ≤ 5% | 上限（超过触发宪法解释层审视） |

---


### §9 RL 权重优化器参数

| 参数 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `KAIROS_RL_LEARNING_RATE` | 0.07 | RL 学习率 |
| `KAIROS_RL_DECAY_FACTOR` | 0.97 | EMA 衰减因子 |
| `KAIROS_RL_MAX_BUFFER_SIZE` | 50 | 反馈缓冲上限 |
| `KAIROS_RL_WEIGHT_RELEVANCE` | 0.4 | RL 相关性权重初始值 |
| `KAIROS_RL_WEIGHT_RECENCY` | 0.2 | RL 新鲜度权重初始值 |
| `KAIROS_RL_WEIGHT_FREQUENCY` | 0.15 | RL 频率权重初始值 |
| `KAIROS_RL_WEIGHT_USER_FEEDBACK` | 0.15 | RL 用户反馈权重初始值 |
| `KAIROS_RL_WEIGHT_TRUST_SCORE` | 0.10 | RL 可信度权重初始值 |

### §10 遗忘与检索参数

| 参数 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `KAIROS_FORGETTING_HALF_LIFE` | 69 | 遗忘半衰期（天） |
| `KAIROS_FRESHNESS_ACTIVE_THRESHOLD` | 0.3 | 活跃记忆 freshness 下限 |
| `KAIROS_FRESHNESS_STALE_THRESHOLD` | 0.1 | 归档记忆 freshness 下限 |
| `KAIROS_DOMAIN_KEYWORDS_PATH` | `~/.kairos/domain_keywords.yaml` | 领域知识库路径 |

## 二、运行时动态调整规则

架构中所有可配置参数支持两类调整模式：

| 模式 | 授权者 | 约束 |
|:-----|:-------|:-----|
| **运维静态配置** | 运维/部署者 | 通过环境变量或配置文件设定，重启生效 |
| **元认知层动态调参** | 元认知层治理器族 | 仅在宪法级约束范围内调整，且受元审计子层监测。每秒调参不超过 1 次 |
| **外部校准驱动调整** | 宪法主权面外部校准端口 | 可临时覆盖任意参数值，覆盖有效期随校准信号生命周期 |

**动态调参不变量（任何时候均不得违反）：**
1. 安全红线（S-01~S-19）阈值不可调低
2. 跨层三环不变量（§8.1）不可被调参破坏
3. 辞典式排序优先级链不受动态调参影响（受 CONSTITUTIONAL_LOCK_PERIOD 保护）

---

## 版本记录

| 版本 | 日期 | 变更 |
|:----|:----|:-----|
| v1.0.0 | 2026-07-18 | Kairos 配置参数参考。§1:4项，§2:9项，§3:9项，§4:24项，§5:7项，§6:2项，§7:9项（含SSRF+WAL），§8.1:5项，§8.3:11项，§8.4:1项，§8.5:1项，§9:8项，§10:4项 = 95 项参数。含运行时动态调整规则与不变量。 |
