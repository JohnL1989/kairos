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

> **文档定位：** 本指南描述 Kairos 的部署模式、配置项、数据目录结构和运维基础。不包含系统架构设计（见 `docs/foundation/architecture-v1.0.0.md`）或可靠性策略（见 `docs/ops/reliability.md`）。
>
> **⚠ 草稿完善声明**：以下部署步骤（`pip install kairos`、`kairos/kairos:latest` 等）为目标示例。当前草稿完善阶段期无构建产物或 Docker 镜像，部署命令将在代码启动后交付。

---

## 一、三级部署模式

| 维度 | 轻量模式 | 标准模式 | 全量模式 |
|:-----|:--------|:--------|:--------|
| **安装方式** | `pip install kairos && kairos serve` | `docker compose up -d` | `docker compose -f docker-compose.full.yml up -d` |
| **数据库** | SQLite + sqlite-vec | PostgreSQL + pgvector | PostgreSQL + pgvector |
| **启动时间** | ~10 秒 | ~10 秒 | ~15 秒 |
| **记忆容量** | 10 万条 | 100 万条 | ≥100 万条 |
| **升华层** | 受限（空闲单线） | 可用 | 完整多线 |
| **策略层** | 内置（使用权重衰减） | 完整激活调度 | 完整 + 探索投资 |
| **元认知层** | — | — | 完整监测器族 |
| **适用场景** | 个人开发、试用心 | 正式生产 | 全功能部署 |

三种模式下所有核心功能等价，仅容量、启动时间和认知能力深度不同。各模式间 API 兼容，切换只需要更改配置文件中的数据源指向和部署方式。

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
| `KAIROS_DB_DSN` | 标准模式必填；轻量模式（SQLite）自动创建 | `sqlite:///data/kairos.db`（轻量模式） | 数据库连接串 |
| `KAIROS_DB_PASSWORD` | 标准模式需 | — | PostgreSQL 密码（docker-compose 部署用，非 DSN 内部含密码时不需要） |
| `KAIROS_API_KEY` | 是 | — | API 认证密钥 |
| `KAIROS_SALT` | 是 | — | PBKDF2 盐值（S-05） |
| `KAIROS_SECRET_KEY` | 是 | — | AES-256-GCM 敏感字段加密密钥 |
| `KAIROS_AUDIT_HMAC_KEY` | 是 | — | HMAC-SHA256 审计链签名密钥 |

> **密钥生成引导**：以上四个 `KAIROS_*` 密钥均可通过 `kairos init --init-key` 一次性生成并写入环境文件，无需手动逐一配置。详见 `user-guide.md` §1.2。
| `KAIROS_LLM_API_KEY` | 是 | — | LLM 供应商 API Key |
| `KAIROS_LLM_ENDPOINT` | 是 | — | LLM 供应商端点 |
| `KAIROS_ADMIN_IPS` | 生产推荐 | — | 管理端点 IP 白名单 |
| `KAIROS_SCHEDULER_INTERVAL` | 否 | 300s | 调度器检查周期 |
| `KAIROS_DAILY_BUDGET_FEN` | 否 | 20000 | LLM 日预算上限（分） |
| `KAIROS_CORE_LIMIT_BYTES` | 否 | 25KB | 常驻契约索引上限 |
| `KAIROS_CORE_LIMIT_LINES` | 否 | 200 | 常驻契约索引行数上限 |
| `KAIROS_SEARCH_DEFAULT_LIMIT` | 否 | 5 | 默认召回上限 |
| `KAIROS_RATE_LIMIT_WRITE_PER_MIN` | 否 | 60 | 写操作限流（单客户端级别） |
| `KAIROS_RATE_LIMIT_READ_PER_MIN` | 否 | 120 | 读操作限流 |
| `KAIROS_INPUT_LIMIT_CONTENT_BYTES` | 否 | 65536 | 单条内容上限（字节） |
| `KAIROS_SSRF_ALLOWED_HOSTS` | 生产推荐 | `api.deepseek.com` | 出站 URL 白名单 |
| `KAIROS_WAL_ARCHIVE_COMMAND` | 否 | `cp %p ~/.kairos/wal_archive/%f` | WAL 归档命令 |

---

## 四、启动与健康检查

轻量模式：
```bash
kairos serve              # 默认 SQLite 模式
kairos serve --pg         # PostgreSQL 模式
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

---

## 五、Docker 部署参考

```yaml
# docker-compose.yml
services:
  kairos:
    image: kairos/kairos:latest
    ports:
      - "127.0.0.1:8010:8010"
    environment:
      - KAIROS_DB_DSN=postgresql://kairos:${KAIROS_DB_PASSWORD}@db:5432/kairos
      - KAIROS_API_KEY=${KAIROS_API_KEY}
      - KAIROS_SALT=${KAIROS_SALT}
      - KAIROS_SECRET_KEY=${KAIROS_SECRET_KEY}
      - KAIROS_AUDIT_HMAC_KEY=${KAIROS_AUDIT_HMAC_KEY}
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
kairos init --db       # 创建表结构（init 含 db init 和 migrate）
kairos db migrate     # 执行迁移
kairos db verify      # 验证数据完整性
kairos db backup      # 手动备份
```

迁移文件位于 `~/.kairos/migrations/`，按时间戳命名。支持回滚。

---

## 七、日志与监控

Kairos 输出结构化 JSON 日志到 stdout（容器部署模式）；本地运行时同时写入 `~/.kairos/logs/`（按日轮转，保留 30 天）。日志格式见 observability.md §二。

```json
{"level":"info","timestamp":"2026-07-18T10:00:00Z","component":"scheduler","message":"sublimation stage 2 completed","events_processed":42}
```

日志级别：`debug` / `info` / `warn` / `error`。通过 `KAIROS_LOG_LEVEL` 环境变量配置（取值范围 `debug|info|warn|error`）。

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
