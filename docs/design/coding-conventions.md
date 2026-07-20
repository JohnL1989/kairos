---
title: Kairos 开发规范
aliases:
  - 开发规范
  - Coding Conventions
tags:
  - kairos
  - development
  - conventions
created: 2026-07-20
updated: 2026-07-20
status: v1.0.0
---

# Kairos 开发规范

> **定位**：Kairos 项目代码编写约定。防止实现漂移，降低多模块协作成本。

---

## 一、命名规范

| 类型 | 规范 | 示例 |
|:----|:-----|:-----|
| Python 模块 | snake_case | `memory_store.py`, `sublimation_pipeline.py` |
| Python 类 | PascalCase | `ForgettingScheduler`, `DictionaryOrderer` |
| Python 函数/方法 | snake_case | `calculate_forgetting_score()`, `trigger_differential_check()` |
| Python 变量 | snake_case | `activation_weight`, `last_calibrated_at` |
| 常量 | UPPER_SNAKE | `MAX_PROTOCOL_COUNT = 10` |
| 事件类型 | snake_case | `memory_write`, `calibration_arrival` |
| 配置键 | UPPER_SNAKE | `KAIROS_DAILY_BUDGET`, `FORGETTING_SCORE_THRESHOLD` |
| 路径键 | kebab-case（路径段） | `kairos://users/default/core/` |
| 数据库列 | snake_case | `usage_count`, `is_identity` |
| JSON 字段 | snake_case | 同 Python |
| 异步函数 | `async def` + `_async` 后缀（仅在函数名不足以表达异步性时） | `async def retrieve_memories(...)` |
| 协程变量 | `task` 前缀 | `task_sublimation`, `task_forgetting` |
| 异步上下文管理器 | `async with` | `async with db.session():` |
| Litestar handler | `@post`/`@get` + `async def` | 见 api-spec.md 示例 |

## 二、项目结构

```
kairos/
├── src/
│   ├── __init__.py
│   ├── main.py                  # CLI 入口
│   ├── config.py                # 配置加载
│   ├── sovereignty/             # 宪法主权面
│   ├── metacognition/           # 元认知层
│   ├── strategy/                # 策略层 (PM)
│   ├── storage/                 # 存储层
│   │   ├── models.py            # 数据模型定义
│   │   ├── memory_store.py      # 记忆 CRUD
│   │   ├── path_index.py        # 路径空间索引
│   │   ├── vector_index.py      # 向量索引
│   │   ├── relation_index.py    # 关系索引
│   │   ├── dual_copy.py         # 双副本管理
│   │   ├── sublimation.py       # 升华管道
│   │   └── forgetting.py        # 遗忘调度器
│   ├── wm/                      # 工作记忆层
│   ├── access/                  # 接入层 (API/CLI/Tools)
│   ├── supervision/             # 监督平面
│   ├── events/                  # 事件总线
│   └── utils/                   # 工具函数
├── tests/
│   ├── unit/                    # 单元测试
│   ├── integration/             # 集成测试
│   └── e2e/                     # 端到端测试
├── docs/                        # 文档
├── migrations/                  # 数据库迁移
└── ops/                         # 部署配置
```

## 三、错误处理模式

| 场景 | 模式 | 示例 |
|:----|:-----|:-----|
| 层内错误 | 抛出异常 | `raise StorageLayerError("memory not found")` |
| 层间传播 | 事件总线异常事件 | 发送 `error_event`，不抛异常出层 |
| 输入验证 | 返回 4xx | API 层返回结构化错误响应 |
| 不可恢复错误 | 记录日志 + 进入降级 | 健康计数器触发降级信号 |
| 安全红线违反 | 拒绝 + 审计日志 | 调用 `audit_log.record()` + `return 403` |

## 四、日志规范

| 字段 | 说明 | 示例 |
|:----|:-----|:-----|
| `level` | debug/info/warn/error | `info` |
| `time` | ISO 8601 | `2026-07-20T10:00:00Z` |
| `component` | 来源组件 | `forgetting_scheduler` |
| `message` | 可读描述 | `forgetting score threshold reached` |
| `memory_id` | 关联记忆 ID | `uuid` |
| `event_id` | 关联事件 ID | `uuid` |
| `error_code` | 错误码 | `ERR-DB-001` |

**日志级别建议**：
- `debug`：开发调试信息，默认不输出
- `info`：常规操作（写入/检索/升华/遗忘）
- `warn`：异常但不影响运行（校准中断、偏置接近阈值）
- `error`：影响功能的错误（数据库断连、组件故障）

## 五、注释与文档字符串

- 模块级 docstring：描述模块职责和主要类
- 公共 API docstring：参数、返回值、异常
- 复杂算法注释：说明算法选择理由（非"做了什么"而是"为什么这么做"）
- 安全红线注释：每条红线的实现位置标注 `# S-NN`

---

## 版本记录

| 版本 | 日期 | 变更 |
|:----|:----|:-----|
| v1.0.0 | 2026-07-20 | 初始开发规范。命名/结构/错误处理/日志/注释。 |
