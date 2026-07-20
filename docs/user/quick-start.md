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
status: v1.0.0
---

# Kairos 快速入门

> **定位**：5 分钟跑通 Kairos 最小闭环。无需 PostgreSQL，轻量模式（SQLite）开箱即用。

---

## 前置条件

- Python ≥ 3.11
- pip 或 uv

## 第一步：安装

```bash
pip install kairos
```

## 第二步：初始化

```bash
# 轻量模式——使用 SQLite，零配置
kairos init --db sqlite:///data/kairos.db
```

## 第三步：启动

```bash
kairos serve --port 8010
```

看到输出 `Kairos started on http://localhost:8010` 即启动成功。

## 第四步：写入一条记忆

```bash
kairos write kairos://playground/ \
  --content "Kairos 快速入门测试记忆" \
  --contract permanent
```

输出应类似：
```
写入成功：abc-def-123-456
```

## 第五步：检索

```bash
kairos search "快速入门" --limit 5
```

输出应返回刚写入的记忆。

## 第六步：浏览路径空间

```bash
kairos tree kairos://playground/ --depth 3
kairos ls kairos://playground/
```

## 第七步：查看系统状态

```bash
kairos status
```

输出应显示各组件的健康状态。

---

## 完成

你已完成 Kairos 的最小闭环：写入 → 检索 → 路径浏览。全部操作约 2 分钟。

> 下一步：阅读 `kairos/user-guide.md` 了解核心操作。
> 部署生产环境：使用标准模式（PostgreSQL + pgvector），见 `kairos/ops/deployment.md`。

---

## 版本记录

| 版本 | 日期 | 变更 |
|:----|:----|:-----|
| v1.0.0 | 2026-07-20 | 初始快速入门。轻量模式 7 步闭环。 |
