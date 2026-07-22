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
status: draft
---

# RL 权重优化器规格

> **定位**：定义七级辞典式排序链之上可学习的二次排序权重维度、初始化策略与更新算法。
> 详见 `foundation/architecture-v1.0.0.md §10.14`。

## 权重维度

| 权重 | 范围 | 默认值 | 受哪些来源影响 | 说明 |
|:----|:----:|:------:|:--------------|:-----|
| `relevance` | 0.30–0.50 | 0.40 | user, knowledge, research | 查询与记忆的语义相关性 |
| `recency` | 0.15–0.25 | 0.20 | context, task_history | 记忆新鲜度 |
| `frequency` | 0.10–0.20 | 0.15 | experience | 访问频率 |
| `user_feedback` | 0.10–0.20 | 0.15 | user | 用户显式反馈（👍/👎） |
| `trust_score` | 0.05–0.15 | 0.10 | knowledge, experience, research | 来源可信度 |

所有权重初始化为范围内随机值，再经 Softmax 归一化。

## 更新算法

### 反馈收集

`POST /v1/feedback（v1.0 为 planned 端点，由 memories_search 的隐式反馈替代）` 接收用户反馈（positive/negative），携带当前检索上下文。

### 权重更新

```
1. 累积 N 条反馈后进入更新（N = KAIROS_RL_MAX_BUFFER_SIZE）
2. 计算基线奖励：近期 20 条反馈的加权平均（线性权重 0.5~1.0）
3. 每条反馈的 Advantage = raw_reward - baseline
4. Reward Contribution Weighting：按来源类型聚合 rel×trust 得分 → Softmax 归一化 → 映射到权重维度
5. delta = learning_rate × advantage × rcw_multiplier
6. 权重 += delta
7. Cosine 学习率衰减：lr = lr_min + 0.5×(1+cos(π×step/max_steps))×(base_lr - lr_min)
8. Epsilon-greedy 探索：eps 从 0.1 线性衰减至 0.01
9. Softmax 重归一化所有权重
10. EMA 平滑：ema = decay × ema + (1-decay) × weights
```

### KL 散度策略追踪

监测权重分布变化，防止策略震荡：
- 计算当前 EMA 权重与快照的 KL 散度（双向取最大值）
- 散度 > 2.0 时，衰减因子额外降低（max_extra=0.3）

## 持久化

权重写入 `rl_weights` 表（按 user_id/profile 隔离，重启后自动恢复）。**注意：** `rl_weights` 存储于 user_profiles 表的 JSONB 字段中（详见 data-model.md user_profiles 表），无需独立表，代码实现时需在 data-model 中补充。
