---
title: Kairos 可观测性设计
aliases:
  - 可观测性
  - Observability
tags:
  - kairos
  - ops
  - monitoring
created: 2026-07-20
updated: 2026-07-20
status: v1.0.0
---

# Kairos 可观测性设计

> **定位**：定义 Kairos 系统的指标体系、结构化日志 schema、告警规则。架构文档定义了「做什么」，本文定义「如何看见做了什么」。

---

## 一、指标体系

### 1.1 运行时指标

| 指标 | 类型 | 说明 | 标签 |
|:----|:----|:-----|:-----|
| `kairos_memory_count` | Gauge | 当前存储记忆总数 | layer, contract |
| `kairos_write_total` | Counter | 写入操作累计次数 | contract, status |
| `kairos_read_total` | Counter | 检索操作累计次数 | method(path/semantic) |
| `kairos_write_duration_ms` | Histogram | 写入延迟 | contract |
| `kairos_read_duration_ms` | Histogram | 检索延迟 | method |
| `kairos_event_bus_queue_depth` | Gauge | 事件总线队列深度 | priority |
| `kairos_sublimation_stage` | Gauge | 升华管道各阶段计数 | stage |
| `kairos_forgetting_score` | Gauge | 遗忘得分分布 | bucket |
| `kairos_budget_remaining_fen` | Gauge | LLM 日预算剩余（分） | provider |
| `kairos_calibration_last_arrival` | Gauge | 距上次校准信号到达的秒数 | source |
| `kairos_degradation_mode` | Gauge | 当前降级模式（0=正常 1=静默 2=受限验证 3=安全休眠） | — |

### 1.2 健康检查

**`GET /health`** 返回：

```json
{
  "status": "ok | degraded | down",
  "components": {
    "api": {"status": "ok", "latency_ms": 2},
    "db": {"status": "ok", "pool_connections": 5, "pool_available": 3},
    "scheduler": {"status": "running", "last_tick": "2026-07-20T10:00:00Z"},
    "embedding": {"status": "ok", "model": "text-embedding-3-small"},
    "sublimation": {"status": "idle", "queue_length": 0},
    "calibration": {"status": "active", "last_arrival": "2026-07-20T09:55:00Z", "mode": "normal"}
  },
  "uptime_seconds": 3600
}
```

## 二、日志 Schema

每个日志条目为 JSON 行（JSON Lines 格式），固定字段：

```json
{
  "timestamp": "2026-07-20T10:00:00.000Z",
  "level": "info",
  "logger": "kairos.storage.forgetting",
  "message": "forgetting score threshold reached",
  "module": "forgetting_scheduler",
  "function": "scan_and_forget",
  "line": 42,
  "memory_id": "abc-def-123",
  "forgetting_score": 0.87,
  "event_id": "uuid-456",
  "duration_ms": 15,
  "error_code": null,
  "trace_id": "trace-789"
}
```

## 三、告警规则

| 告警名 | 条件 | 严重度 | 响应 |
|:-------|:-----|:-------|:-----|
| 数据库断连 | 健康检查连续 3 次失败 | critical | 人工介入 |
| 写入延迟飙升 | P95 > 500ms 持续 5 分钟 | warning | 检查嵌入服务 |
| 检索延迟飙升 | P95 > 800ms 持续 5 分钟 | warning | 检查 pgvector 索引 |
| 校准中断警告 | 距上次校准 > N 周期 | info | 检查校准源 |
| 校准中断严重 | 距上次校准 > M 周期 | warning | 触发降级 |
| 偏置告警 | 来源多样性收敛或校准衰减超阈 | warning | 人工审查 |
| 正反馈告警 | 偏置在加速放大 | critical | 宪法解释层介入 |
| 身份偏置告警 | 身份一致性记忆系统性压制异质记忆 | warning | 人工审查 |
| 冻结超时 | 冻结持续超过预设时长 | critical | 自动告警至外部管理员 |
| 预算耗尽 | LLM 日预算余额 < 10% | info | 等待预算重置或充值 |

## 四、元认知层检测器输出可见性

| 检测器 | 输出 | 外部可见性 |
|:-------|:-----|:----------|
| 流形曲率/密度 | 几何拓扑报告 | 通过审计日志 |
| 分布偏移 | 偏移量 + 方向 | 通过事件总线告警 |
| 盲区标注 | 盲区地图 | 只读 API |
| 叙事连贯性 | 趋势报告 | 通过校准端口 |
| 来源混淆/图式同化 | 告警（预留） | v1.1 启用 |
| 偏置放大率 | 正反馈告警 | 监督平面专用信道 |
| 自我参照效应 | 身份偏置告警 | 监督平面专用信道 |
| 耦合计 | 轴耦合告警 | 监督平面专用信道 |
| VAD 独立性 | 独立性证伪信号 | 监督平面专用信道 |

---

## 版本记录

| 版本 | 日期 | 变更 |
|:----|:----|:-----|
| v1.0.0 | 2026-07-20 | 初始可观测性设计。指标/日志/告警/检测器可见性。 |
