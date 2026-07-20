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
status: v1.0.0
---

# Kairos 用户指南

> **定位**：面向 Agent 开发者的操作文档。deployment 解决「怎么装」，本文解决「怎么用」。

---

## 一、快速上手

### 1.1 安装

```bash
# 标准模式（需要 PostgreSQL）
pip install kairos
kairos init --db postgresql://localhost:5432/kairos

# 轻量模式（SQLite，开箱即用）
pip install kairos
kairos init --db sqlite:///data/kairos.db
```

### 1.2 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|:----|:----|:-------|:-----|
| `KAIROS_API_KEY` | ✅ | — | API Key（read/write/admin 三级） |
| `KAIROS_DB_URL` | ✅ | — | 数据库连接 URL |
| `KAIROS_LLM_API_KEY` | ❌ | — | LLM Provider API Key (升华/嵌入) |
| `KAIROS_DAILY_BUDGET_FEN` | ❌ | 20000 | LLM 日预算（分，20000分=200元） |

### 1.3 启动

```bash
kairos serve --port 8010
# 输出：Kairos started on http://localhost:8010
```

---

## 二、核心操作

### 2.1 写入记忆

```python
# 使用 KairosClient
from kairos import KairosClient

client = KairosClient(api_key="sk-...")

# 写入一条按需记忆
memory = client.write(
    path="kairos://sessions/abc123/",
    content="用户偏好：暗色主题",
    contract="ondemand",       # 可选：permanent / ondemand / environmental / temporary
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
- 通过环境变量 `KAIROS_SEED_PATH` 指定种子目录
- 种子应尽量少而精确（最小化原则）
- 系统会在运行中逐步退化为自产数据驱动

---

## 四、限制与约束

| 项 | 限制 | 绕过 |
|:----|:-----|:-----|
| 单条内容上限 | 64 KB | 分割为多条关联记忆 |
| 路径深度 | ≤ 10 层 | 超深层路径自动截断 |
| 单次检索返回条数 | ≤ 100 | 分页（offset/limit） |
| 并发写入 | ≤ 100 ops/s | 队列缓冲 |
| 单 API Key 分级 | 三级权限预置 | 多 Key 轮换 |
| 外部校准中断持续 | 超过配置阈值（DEGRADATION_PERIOD）周期进入安全休眠 | 恢复校准信号自动退出 |

---

## 版本记录

| 版本 | 日期 | 变更 |
|:----|:----|:-----|
| v1.0.0 | 2026-07-20 | 初始用户指南。上手/核心操作/最佳实践/限制。 |
