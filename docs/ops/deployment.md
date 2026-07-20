---
title: Kairos 部署指南
aliases:
  - Kairos 部署
  - 部署配置
tags:
  - kairos
  - deployment
  - ops
created: 2026-07-18
status: draft
---

# Kairos 部署指南

> **文档定位：** 本指南描述 Kairos 的部署模式、配置项、数据目录结构和运维基础。不包含系统架构设计（见 `docs/kairos/architecture-v1.0.0.md`）或可靠性策略（见 `docs/kairos/ops/reliability.md`）。

---

## 一、双部署模式

| 维度 | 轻量模式 | 标准模式 |
|:-----|:--------|:--------|
| **安装方式** | `pip install kairos && kairos start` | `docker compose up -d` |
| **数据库** | SQLite + sqlite-vec | PostgreSQL + pgvector |
| **启动时间** | ~10 秒 | ~30 秒 |
| **记忆容量** | 5 万条 SLO | 100 万条 SLO |
| **升华层** | 可用 | 可用 |
| **调度层** | 内置 | 内置 + 外部调度器可选 |
| **适用场景** | 个人开发、试用心 | 正式生产 |

两种模式下所有功能等价，仅容量和并发能力不同。存储层接口统一，切换只需要更改配置文件中的数据源指向。

---

## 二、数据目录

```
~/.kairos/
├── kairos/                  路径空间根目录（内存映射 + 持久化）
├── core/                    常驻契约 · 索引+文件
├── memories/                按需契约 · 向量存储
├── sessions/                按需契约 · 对话日志
├── strategies/              升华产物
├── archive/                 过期数据
└── backups/
    └── core/                常驻契约备份
```

---

## 三、环境变量

| 变量 | 必填 | 默认值 | 说明 |
|:----|:----|:-------|:-----|
| `KAIROS_DB_DSN` | 是 | — | 数据库连接串 |
| `KAIROS_API_KEY` | 是 | — | API 认证密钥 |
| `KAIROS_API_KEY_SALT` | 是 | — | PBKDF2 盐值 |
| `KAIROS_MASK_KEY` | 是 | — | AES-256-GCM 脱敏密钥 |
| `KAIROS_LLM_API_KEY` | 是 | — | LLM 供应商 API Key |
| `KAIROS_LLM_ENDPOINT` | 是 | — | LLM 供应商端点 |
| `KAIROS_ADMIN_IPS` | 生产推荐 | — | 管理端点 IP 白名单 |
| `KAIROS_SCHEDULER_INTERVAL` | 否 | 300s | 调度器检查周期 |
| `KAIROS_DAILY_BUDGET` | 否 | 140 | LLM 日预算上限（分） |
| `KAIROS_CORE_LIMIT_BYTES` | 否 | 25KB | 常驻契约索引上限 |
| `KAIROS_CORE_LIMIT_LINES` | 否 | 200 | 常驻契约索引行数上限 |
| `KAIROS_SEARCH_DEFAULT_LIMIT` | 否 | 5 | 默认召回上限 |

---

## 四、启动与健康检查

轻量模式：
```bash
kairos start              # 默认 SQLite 模式
kairos start --pg         # PostgreSQL 模式
kairos health             # 健康检查
```

标准模式：
```bash
docker compose up -d       # 启动全部服务
docker compose logs -f     # 查看日志
curl http://localhost:8010/health  # 健康检查端点
```

健康检查返回 JSON，包含各组件状态：
```json
{
  "status": "ok",
  "components": {
    "api": "ok",
    "db": "ok",
    "scheduler": "running",
    "embedding": "ok",
    "sublimation": "idle",
    "calibration": "active"
  },
  "uptime_seconds": 3600
}
```

---

## 五、Docker 部署参考

```yaml
# docker-compose.yml
services:
  kairos:
    image: kairos/kairos:latest
    ports:
      - "8010:8010"
    environment:
      - KAIROS_DB_DSN=postgresql://user:pass@db:5432/kairos
      - KAIROS_API_KEY=${KAIROS_API_KEY}
      - KAIROS_API_KEY_SALT=${KAIROS_API_KEY_SALT}
      - KAIROS_MASK_KEY=${KAIROS_MASK_KEY}
      - KAIROS_LLM_API_KEY=${KAIROS_LLM_API_KEY}
      - KAIROS_LLM_ENDPOINT=${KAIROS_LLM_ENDPOINT}
    volumes:
      - ~/.kairos:/root/.kairos
    depends_on:
      - db
  db:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_DB=kairos
      - POSTGRES_USER=kairos
      - POSTGRES_PASSWORD=${KAIROS_DB_PASSWORD}
    volumes:
      - kairos_db:/var/lib/postgresql/data

volumes:
  kairos_db:
```

---

## 六、数据库初始化

轻量模式（SQLite）自动创建数据库和表结构。启动时自动执行迁移。

标准模式（PostgreSQL）：
```bash
kairos db init        # 创建表结构
kairos db migrate     # 执行迁移
kairos db verify      # 验证数据完整性
kairos db backup      # 手动备份
```

迁移文件位于 `~/.kairos/migrations/`，按时间戳命名。支持回滚。

---

## 七、日志与监控

Kairos 输出结构化 JSON 日志到 stdout：

```json
{"level":"info","time":"2026-07-18T10:00:00Z","component":"scheduler","message":"sublimation stage 2 completed","events_processed":42}
```

日志级别：`debug` / `info` / `warn` / `error`。通过 `KAIROS_LOG_LEVEL` 环境变量配置。

---

## 八、版本升级

```bash
# 轻量模式
pip install --upgrade kairos
kairos db migrate       # 执行数据库迁移

# 标准模式
docker compose pull kairos
docker compose up -d    # 自动重建
kairos db migrate       # 执行数据库迁移
```

升级前建议先备份数据库。降级需使用旧镜像 + 回滚迁移。
