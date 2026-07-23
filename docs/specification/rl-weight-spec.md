---
title: RL 权重优化器规格
aliases:
  - RL 权重
  - rl-weight-spec
tags:
  - kairos
  - rl
  - specification
created: 2026-07-22
updated: 2026-07-23
status: draft
---

# RL 权重优化器规格

> **定位**：定义六级辞典式排序链+身份面否决权之上可学习的二次排序维度、更新算法与 P6 合规框架。
> 详见 `foundation/architecture-v1.0.0.md §10.14`。
>
> **P6 合规声明**：本规格采用**多维独立排序**（各维度不聚合为单标量参与裁决），符合 P6 「价值裁决禁止单标量聚合」的绝对禁令。各维度在辞典式排序链内独立产出排序信号，交叉约束由维度间的全局闸门管理。

## 排序维度

| 维度 | 目标权重范围 | 默认值 | 受来源影响 | 说明 |
|:----|:-----------:|:------:|:----------|:-----|
| `relevance` | 0.30–0.50 | 0.40 | user, knowledge, research | 查询与记忆的语义相关性 |
| `recency` | 0.15–0.25 | 0.20 | context, task_history | 记忆新鲜度 |
| `frequency` | 0.10–0.20 | 0.15 | experience | 访问频率 |
| `user_feedback` | 0.10–0.20 | 0.15 | user | 用户显式反馈（👍/👎） |
| `trust_score` | 0.05–0.15 | 0.10 | knowledge, experience, research | 来源可信度 |

## 多维排序算法

辞典式排序链是主排序（第一优先），RL 权重是**二级多维排序**（在各辞典链层级内部使用）。排序过程：

```
1. 辞典式排序链裁决：按 身份>探索>宪法>校准>认知完整性>时间>间接度 分层
2. 每层内的二级排序由五维信号独立参与：
   a. 各维度独立产出排序分（不加权求和）
   b. 维度间的关系由 P6 全局闸门约束（见§P6合规段）
   c. 检索排序器接收五维独立信号，按字典序逐维裁决
3. 跨维冲突（如相关性和新鲜度指向不同结果）由辞典式优先级解决：
   relevance < recency < frequency < user_feedback < trust_score
```

### 初始化

各维度独立初始化到目标范围中位数。不做 simplex 归一化（和≠1 是正常的——各维度独立运作）。

### 维度权重更新

```
1. 累积 N 条反馈后进入更新（N = KAIROS_RL_MAX_BUFFER_SIZE）
2. 每条反馈携带各维度的独立评分（不合并为总分）
3. 按来源类型聚合 rel×trust 得分 → 各维度独立 delta
4. Cosine 学习率衰减：lr = lr_min + 0.5×(1+cos(π×step/max_steps))×(base_lr - lr_min)
5. Epsilon-greedy 探索：eps 从 0.1 线性衰减至 0.01
6. 各维度独立 clamp 到目标范围
7. EMA 平滑：each_dim_ema = decay × each_dim_ema + (1-decay) × each_dim_weight
```

### KL 散度策略追踪

监测各维度权重分布变化，防止策略震荡：
- 计算当前 EMA 权重与快照的 KL 散度（各维度独立计算，取最大值为总体散度）
- 总体散度 > 0.5 时，衰减因子额外降低（max_extra=0.3）

## P6 合规框架

| 检查项 | 状态 | 证据 |
|:-------|:----|:-----|
| 禁止单标量聚合参与价值裁决 | ✅ 合规 | 五维独立排序，不加权求和 |
| 维度间交叉约束有全局闸门 | ✅ 合规 | 辞典式优先级 + 独立 clamp 范围 |
| 信息损失显式标注 | ✅ 合规 | 各维度独立输出，不聚合 |
| 可回溯的多维表征 | ✅ 合规 | 每次排序记录五维独立得分 |

## 持久化

五维权重以 JSONB 存储于 `user_profiles` 表的 `rl_weights` 字段中（按 user_id/profile 隔离，重启后自动恢复）。权重维度：`{"relevance": 0.40, "recency": 0.20, "frequency": 0.15, "user_feedback": 0.15, "trust_score": 0.10}`。代码实现时需在 data-model.md user_profiles 表补充该字段定义。
