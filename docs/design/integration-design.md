---
title: Kairos 集成设计
aliases:
  - 集成设计
  - Integration Design
tags:
  - kairos
  - design
  - integration
created: 2026-07-20
updated: 2026-07-20
status: v1.0.0
---

# Kairos 集成设计

> **定位**：定义 Kairos 与宿主 Agent 的交互全生命周期。覆盖会话初始化、写入、检索、升华、事件回调、错误传播语义、并发约束、超时契约。

---

## 一、Agent 集成流程

```
Agent 应用
  │
  ├── 初始化 ──→ KairosClient(config)
  │                 ├── api_key (read/write/admin)
  │                 ├── base_url (默认 localhost:8010)
  │                 └── timeout (默认 30s)
  │
  ├── 写入 ──→ client.write(path, content, contract, ...)
  │                 └── 返回 memory_id
  │
  ├── 检索 ──→ client.search(query, path, limit)
  │                 └── 返回 Memory 对象列表
  │
  ├── 浏览 ──→ client.browse(path, depth)
  │                 └── 返回路径树
  │
  └── 关闭 ──→ client.close()
```

## 二、同步与异步

| 操作 | 推荐模式 | 超时 | 说明 |
|:----|:--------|:----|:-----|
| 写入 | 同步 | 10s | 嵌入计算在写入时同步完成 |
| 检索 | 同步 | 10s | 路径索引查询 + 可选的向量搜索 |
| 批量导入 | 异步 | — | 返回 job_id，轮询进度 |
| 升华触发 | 异步 | — | 空闲调度，不阻塞 Agent |
| 校准信号 | 同步 | 5s | 见证锚定更新需确认 |
| 冻结 | 同步 | 5s | 强制操作需确认 |
| 配置修改 | 同步 | 5s | 运行时参数热更新 |

## 三、并发约束

| 场景 | 约束 | 违反后果 |
|:----|:-----|:---------|
| 同一记忆并发写入 | 最后写入者胜出（version 递增） | 旧版本标记 superseded |
| 同一记忆并发检索 | 无锁，顺序执行 | — |
| 遗忘与检索并发 | 遗忘不阻塞检索（标记后清除） | 已遗忘的记忆不被返回 |
| 升华与写入并发 | 升华读取快照，写入不阻塞 | 升华延迟一个周期 |
| 外部校准与内部使用并发 | 校准优先（强一致） | 使用权重延迟更新 |
| 冻结期间 | 所有生成性操作拒绝 | 只读操作允许 |

## 四、错误传播语义

| 错误类型 | 传播方式 | Agent 可见性 |
|:--------|:---------|:------------|
| 输入验证失败 | 直接返回 4xx | 可见 |
| 存储层异常 | 返回 503 + `ERR-DB-*` | 可见（重试建议） |
| LLM 超时 | 返回 503 + `ERR-LLM-*` | 可见（可降级为纯路径检索） |
| 安全红线违反 | 返回 403 + `ERR-SEC-*` | 可见 |
| 层内异常（非传播） | 日志记录 + 降级触发 | 不可见（健康检查可查询） |
| 事件总线背压 | 事件发送方等待（阻塞） | 不可见（延迟增加） |

## 五、事件回调

Kairos 支持通过 Webhook 或事件轮询向 Agent 通知异步事件：

| 事件 | 触发条件 | 建议 Agent 响应 |
|:----|:---------|:---------------|
| `sublimation_awaiting_approval` | behavior 阶段产物待审批 | 用户确认/拒绝 |
| `calibration_degradation` | 外部校准进入降级模式 | 检查校准源 |
| `bias_alert` | 元记忆偏置告警触发 | 人工审查 |
| `freeze_activated` | 强制冻结激活 | 检查系统状态 |
| `seed_lifecycle` | 种子退化/替换 | 确认偏置重置 |

## 六、配置集成

```python
# Agent 集成示例
from kairos import KairosClient

client = KairosClient(
    api_key=os.environ["KAIROS_API_KEY"],
    base_url="http://localhost:8010",
    timeout=30,
)

# 写入
memory = client.write(
    path="kairos://sessions/abc123/",
    content="用户偏好：暗色主题",
    contract="ondemand",
    memory_type="semantic",
)

# 检索
results = client.search("暗色主题", limit=5)
for r in results:
    print(f"{r.path}: {r.content}")
```

---

## 版本记录

| 版本 | 日期 | 变更 |
|:----|:----|:-----|
| v1.0.0 | 2026-07-20 | 初始集成设计。Agent 全生命周期 + 并发约束 + 错误传播 + 事件回调。 |
