---
title: 情感效价 VAD 坐标算法参考
aliases:
  - vad-coordinate-algorithm
tags:
  - kairos
  - reference
  - algorithm
created: 2026-07-19
status: draft
---

# 情感效价 VAD 坐标算法参考

> **对应追缴：** D-027（架构 §4.2 情感效价空间 + §2.2 情感流形监测器）
> **认知基础映射：** 情感作为一阶维度——度量空间 VAD 追踪 + 驱动空间调制

## 一、VAD 三维度定义

每条记忆的元数据纳入 VAD 三维度，值域均为 `[-1.0, 1.0]`：

| 维度 | 含义 | 负值范围 | 正值范围 |
|:----|:-----|:---------|:---------|
| **V** (Valence) | 效价——愉悦/厌恶程度 | -1 = 极厌恶 | +1 = 极愉悦 |
| **A** (Arousal) | 唤醒度——激烈/平静程度 | -1 = 极平静 | +1 = 极激烈 |
| **D** (Dominance) | 支配度——控制/被控程度 | -1 = 极被动 | +1 = 极主动 |

## 二、VAD 映射规则

### 2.1 编码阶段

记忆写入时的初始 VAD 值由以下三因素合成：

```
V_init = 0.3 × V_content + 0.4 × V_context + 0.3 × V_default
A_init = 0.5 × A_content + 0.3 × A_context + 0.2 × A_novelty
D_init = 0.3 × D_content + 0.3 × D_context + 0.4 × D_agency
```

- `V_content` / `A_content` / `D_content`：内容语义的情感推断（由轻量级情感分析模型计算，不可用时默认为 0）
- `V_context` / `A_context` / `D_context`：当前推理上下文的情感状态（由 WM 层当前工作空间的情感基线提供）
- `V_default`：默认厌恶中性值（默认 0.1，偏好轻微正面）
- `A_novelty`：新异度——首次见到的实体/关系类型时 A += 0.3
- `D_agency`：主体性——系统主动决策生成的记忆比被动摄入的记忆 D 更高（主动决策 D += 0.2）

### 2.2 巩固阶段——Arousal → 更新势垒调制

```
N_effective = N_base × (1 + A × modulation_factor)
```

- `N_base`：更新势垒基准值（`WITNESS_UPDATE_BARRIER_N_DEFAULT`，默认 3）
- `A`：记忆自身的 Arousal 值（归一化至 [0, 1] 范围）
- `modulation_factor`：默认 0.3——高唤醒记忆需更多证据方可改写

### 2.3 提取阶段——情感基线提升

预测器在计算检索候选权重时，额外纳入当前上下文与记忆 VAD 向量的余弦相似度作为独立通道：

```
boost = max(0, cos(VAD_context, VAD_memory) - 0.5) × 2.0
```

当 `cos < 0.5` 时 boost 归零。boost 值直接增加记忆在预激活集中的排序权重。

### 2.4 情感去强化

当情感流形监测器检测到某记忆簇在 VAD 空间中的激活预算占比持续超阈值时，触发去强化（见架构 §4.2 整合窗——情感去强化机制）。

## 三、情感漂移检测

情感流形监测器在每个调度周期对 VAD 空间中的记忆簇做拓扑扫描，计算每簇质心的三维坐标偏移量。若偏移量相对于基准点（最近一次外部校准时点的质心坐标）偏离超过 `EMOTIONAL_VAD_DEVIATION_SIGMA`（默认 1.5σ），触发外部校准告警。
