---
title: Kairos 用户指南
aliases:
  - 用户指南
  - User Guide
tags:
  - kairos
  - user
  - guide
created: 2026-07-20
updated: 2026-07-20
status: draft
---

# Kairos 用户指南

> **状态声明**：本文描述的 CLI 命令（`kairos init`、`kairos serve` 等）为**设计目标**。当前代码（`amber/`）为先行实验性实现，使用 FastAPI + asyncpg。CLI 工具尚未构建。本文档作为完整的操作规格，待 CLI 就绪后逐条可执行化。

> **定位**：面向 Agent 开发者的操作文档。deployment 解决「怎么装」，本文解决「怎么用」。`kairos suppress` 为 v1.0 功能。
>
> **⚠ 草稿完善声明**：以下所有命令与 SDK 调用（`pip install kairos`、`from kairos import KairosClient` 等）为设计示例，当前无构建产物、无可执行命令、无 Python SDK。全部 CLI 命令（`kairos write`、`kairos search` 等）为虚构——当前文档处于设计冻结阶段，代码尚未启动。具体命令语法在代码实现后可能变化。读者应关注接口语义而非命令文本。

---

## 一、快速上手

### 1.1 安装

```bash
# 标准模式（需要 PostgreSQL）
pip install kairos
kairos init --db postgresql://localhost:5432/kairos

# 轻量模式（SQLite，开箱即用）
pip install kairos
kairos init --db ~/.kairos/kairos.db
```

### 1.2 首次部署（Key 引导流程）

S-01 要求无有效 Key 拒绝启动。首次部署时需先生成密钥，打破「先有 Key 才能启动」的循环：

```bash
# 1. 初始化密钥（生成全部四个密钥并写入环境文件）
kairos init --init-key

# 2. 初始化数据库
kairos init --db ~/.kairos/kairos.db
```bash
kairos serve --port 8010
```

`--init-key` 生成以下密钥并写入 `~/.kairos/.env`（与 quick-start 一致）：
- `KAIROS_API_KEY` — API 鉴权
- `KAIROS_SECRET_KEY` — 数据加密
- `KAIROS_AUDIT_HMAC_KEY` — 审计链 HMAC
- `KAIROS_SALT` — Salt 密钥（S-05 要求）

> **注意**：`--init-key` 生成全部四个密钥（含 `KAIROS_SALT`）。这四个密钥是首次启动的必要条件——缺少任意一个均拒绝启动。

### 1.3 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|:----|:----|:-------|:-----|
| `KAIROS_SALT` | ✅ | — | Salt 密钥（S-05 要求无 Salt 拒绝启动） |
| `KAIROS_API_KEY` | ✅ | — | API Key（read/write/admin 三级） |
| `KAIROS_SECRET_KEY` | ✅ | — | 数据加密密钥 |
| `KAIROS_AUDIT_HMAC_KEY` | ✅ | — | 审计链 HMAC 密钥 |
| `KAIROS_DB_DSN` | ✅ | — | 数据库连接串 |
| `KAIROS_LLM_API_KEY` | ✅ | — | LLM Provider API Key (升华/嵌入) |
| `KAIROS_DAILY_BUDGET_FEN` | ❌ | 20000 | LLM 日预算（分，20000分=200元） |

### 1.4 启动

```bash
kairos serve --port 8010
# 输出：Kairos started on http://localhost:8010
```

---

## 二、核心操作

### 2.1 写入记忆

```python
# 使用 KairosClient（目标 SDK，当前草稿完善阶段期无构建产物）
from kairos import KairosClient

client = KairosClient(api_key="sk-...")

# 写入一条按需记忆
memory = client.write(
    path="kairos://sessions/abc123/",
    content="用户偏好：暗色主题",
    source="user_input",         # S-15 要求来源标识（合法枚举值见 api-spec provenance 字段）
    contract="ondemand",         # 可选：permanent / ondemand / environmental / temporary
)

print(f"写入成功：{memory.id}")
```

```bash
# 使用 CLI
kairos write kairos://sessions/abc123/ --content "用户偏好：暗色主题" --contract ondemand
```

### 2.2 检索记忆

```python
# 按路径前缀检索
results = client.search(path="kairos://sessions/abc123/")
for r in results:
    print(f"[{r.path}] {r.content}")

# 按语义检索
results = client.search("暗色主题", limit=5)
```

```bash
kairos search "暗色主题" --limit 5
kairos ls kairos://sessions/abc123/
kairos tree kairos://sessions/ --depth 2
```

### 2.3 管理记忆

```bash
# 查看记忆详情
kairos read <memory_id>

# 更新记忆
kairos update <memory_id> --content "更新后内容"

# 显式遗忘
kairos forget <memory_id>

# 定向遗忘（抑制检索但保留数据）
kairos suppress <memory_id> --reason "合规擦除"
```

### 2.4 外部校准

当系统内的记忆见证锚定不准确时，发送校准信号：

```bash
kairos calibrate --memory-id <uuid> --score 0.85
```

查看当前校准状态：
```bash
kairos status
# 输出：校准状态: active | 距上次校准: 120s | 模式: 正常
```

---

## 三、最佳实践

### 3.1 路径规划

- 使用 `kairos://projects/{project_name}/sessions/` 组织项目级记忆
- 使用 `kairos://sessions/{session_id}/` 组织会话级临时记忆
- 使用 `kairos://users/{user_id}/preferences/` 存储用户偏好
- 使用 `kairos://knowledge/` 存储全局知识库

### 3.2 契约选择

| 契约 | 适用场景 | 遗忘行为 |
|:----|:---------|:---------|
| `permanent` | 核心规则、宪法级偏好 | 不遗忘（仅 S-10 见证豁免保护） |
| `ondemand` | 日常写入，默认选项 | 低使用权重时被遗忘 |
| `environmental` | 高相关信息（如当天上下文） | 环境变化时自然过期 |
| `temporary` | 中间状态、临时缓存 | 空闲时优先清理 |

### 3.3 升华利用

系统在空闲时将原始经验（raw）逐步提纯为行为规则（behavior）。建议：
- 定期 `kairos status` 查看升华进度
- behavior 阶段需人工确认（`kairos approve <id>` 或拒绝）
- 升华产物会去语境化，重复经验归约为通用策略

### 3.4 种子锚点

首次启动时系统需要种子锚点作为冷启动参考。建议：
# 种子路径设置
KAIROS_SEED_PATH=~/.kairos/seeds/   # 可选。未设置则使用内置默认种子
- 种子应尽量少而精确（最小化原则）
- 系统会在运行中逐步退化为自产数据驱动

---

## 四、限制与约束

| 项 | 限制 | 绕过 |
|:----|:-----|:-----|
| 单条内容上限 | 64 KB | 分割为多条关联记忆 |
| 路径深度 | ≤ 10 层 | 超深层路径拒绝（返回 400），缩短路径后重试 |
| 单次检索返回条数 | ≤ 100 | 分页（offset/limit） |
| 并发写入 | ≤ 60/min（≈1 ops/s，单客户端令牌桶限流） | 队列缓冲。系统级硬上限 500 ops/s（熔断），系统容量目标 ≥100 ops/s（多客户端并行）。详见 ops/configuration.md §7 |
| 单 API Key 分级 | 三级权限预置 | 多 Key 轮换 |
| 外部校准中断持续 | 超过配置阈值（DEGRADATION_PERIOD）周期进入安全休眠 | 恢复校准信号自动退出 |

---

## 版本记录

| 版本 | 日期 | 变更 |
|:----|:----|:-----|
| v1.0.0 | 2026-07-20 | 初始用户指南。上手/核心操作/最佳实践/限制。 |
