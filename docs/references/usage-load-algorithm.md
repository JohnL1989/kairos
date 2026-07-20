---
title: 使用负载计量器——五类负载算法参考
aliases:
  - usage-load-algorithm
tags:
  - kairos
  - reference
  - algorithm
created: 2026-07-19
status: draft
---

# 使用负载计量器——五类负载算法参考

> **对应追缴：** D-021（架构 §3.2 使用负载计量器）
> **认知基础映射：** 使用价值轴的多维特征空间——目的性维度（检索/验证/贡献）× 方式性维度（模拟/非模拟）× 意识性维度（内隐/外显）

## 一、五维负载向量

每条记忆维护一个五维特征向量 `L = [l_retrieval, l_verification, l_contribution, l_simulation, l_implicit]`，各维度一分量，每次调用对应类型的操作时在对应分量上累加。

**基础负载系数**（见 `ops/configuration.md` `COMPOSITION_*_WEIGHT`）：
| 类型 | 系数 | 说明 |
|:----|:----:|:-----|
| 检索 retrieval | 1.2 | 信息提取，对表征稳定性影响最小 |
| 验证 verification | 1.4 | 比对确认，中等负担 |
| 贡献 contribution | 1.6 | 新增事实，结构性影响 |
| 模拟 simulation | 1.8 | 反事实推演，高负担 |
| 内隐 implicit | 2.0 | 行为偏向沉积，最大影响 |

## 二、影子副本置信度累积

每条记忆的影子副本置信度 `C ∈ [0, 1]` 的累积速率受负载系数约束：

```
ΔC_per_event = base_rate × (1 / load_coefficient)
```

其中 `base_rate` 为基础置信度增长步长（默认 0.01）。

记忆经历的负载越重（系数越高），其置信度增长越慢——需要更长的观察窗口才能积累到合并阈值。

**合并阈值**：`C ≥ MERGE_THRESHOLD`（默认 0.7，见 `SANDBOX_CONFIDENCE_INTEGRATION_THRESHOLD`） 时影子副本可异步合并至主副本。

## 三、P6 合规声明

五维负载向量在帕累托计算中分别独立——候选生成器在五维空间上计算不可支配解集，禁止聚合为单标量（P6）。

负载系数仅影响影子副本置信度累积速率（工程便利），不参与价值裁决。价值裁决仍由五维帕累托空间通过序数可比性决定。
