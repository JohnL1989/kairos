---
title: Kairos 快速入门
aliases:
  - 快速入门
  - Quick Start
tags:
  - kairos
  - user
  - quickstart
created: 2026-07-20
updated: 2026-07-20
status: draft
---

# Kairos 快速入门

> **状态声明**：本文描述的 CLI 命令（`kairos init`、`kairos serve` 等）为**设计目标**，当前代码（`amber/` 目录）为先行实验性实现（FastAPI + asyncpg + pgvector）。CLI 工具尚未构建。若需直接使用现有代码，见 `amber/README.md`。

> **定位**：5 分钟跑通 Kairos 最小闭环。无需 PostgreSQL，轻量模式（SQLite）开箱即用。
>
> **⚠ 草稿完善声明**：以下所有命令（`pip install kairos`、`kairos serve` 等）为目标示例。当前草稿完善阶段期无构建产物或可执行包，命令将在代码启动后交付。

---

## 前置条件

- Python ≥ 3.11
- pip 或 uv
- 设置 `KAIROS_SALT` 环境变量（S-05 要求无 Salt 拒绝启动）。由 `kairos init --init-key` 自动生成，前置条件阶段无需手动设置
- `KAIROS_API_KEY`、`KAIROS_SECRET_KEY`、`KAIROS_AUDIT_HMAC_KEY` 同样由 `init --init-key` 自动生成——前置条件阶段无需手动设置任何密钥

## 第一步：安装

```bash
pip install kairos
```

## 第二步：初始化并生成密钥

```bash
# 初始化数据库并自动生成全部密钥
kairos init --init-key

# init --init-key 自动生成 KAIROS_API_KEY / KAIROS_SALT / KAIROS_SECRET_KEY / KAIROS_AUDIT_HMAC_KEY
# 并写入环境文件（默认 ~/.kairos/.env——密钥文件路径，非 secrets.yaml）
# 启动时自动读取，无需手动 export
```

> S-01 要求无有效 API Key 时系统拒绝所有请求。Key 生成后请妥善保管。

## 第三步：初始化

```bash
# 轻量模式——使用 SQLite，零配置
kairos init --db sqlite:///$HOME/.kairos/kairos.db
```

## 第四步：启动

```bash
kairos serve --port 8010
```

看到输出 `Kairos started on http://localhost:8010` 即启动成功。

## 第五步：写入一条记忆

```bash
kairos write kairos://playground/ \
  --content "Kairos 快速入门测试记忆" \
  --contract ondemand \
  --source user_input
```

输出应类似：
```
写入成功：abc-def-123-456
```

## 第六步：检索

```bash
kairos search "快速入门" --limit 5
```

输出应返回刚写入的记忆。

## 第七步：浏览路径空间

```bash
kairos tree kairos://playground/ --depth 3
kairos ls kairos://playground/
```

## 第八步：查看系统状态

```bash
kairos status
```

输出应显示各组件的健康状态。

---

## 完成

你已完成 Kairos 的最小闭环：写入 → 检索 → 路径浏览。全部操作约 2 分钟。

> 下一步：阅读 `user-guide.md` 了解核心操作。
> 部署生产环境：使用标准模式（PostgreSQL + pgvector），见 `ops/deployment.md`。

---

## 版本记录

| 版本 | 日期 | 变更 |
|:----|:----|:-----|
| v1.0.0 | 2026-07-20 | 初始快速入门。轻量模式 8 步闭环。 |
