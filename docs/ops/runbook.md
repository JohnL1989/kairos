---
title: Kairos 运维手册
aliases:
  - Runbook
  - 运维操作手册
tags:
  - kairos
  - ops
  - runbook
created: 2026-07-21
updated: 2026-07-22
status: draft
---

# Kairos 运维手册

> **定位**：deployment.md 首次部署后的日常操作手册。三个月后不记得怎么备份、升级、恢复时翻这里。
>
> **⚠ 草稿完善声明**：以下 `kairos` 子命令为目标示例。当前文档草稿阶段，无运行代码，命令格式和可用性将在代码启动后最终确认。所有操作以当时版本 CLI 帮助为准。

---

## §1 日常操作

### 1.1 启动与停止

| 模式 | 启动 | 停止 |
|:----|:-----|:-----|
| 轻量模式 | `kairos serve --port 8010` | `Ctrl+C` 或 `kairos stop` |
| 标准模式 | `docker compose up -d` | `docker compose down` |

### 1.2 状态检查

| 命令 | 用途 |
|:----|:-----|
| `kairos status` | 各层运行状态（宪法主权面/元认知/策略/WM/存储/接入） |
| `kairos health` | 健康检查（含数据库连接/LLM 端点/调度器状态） |
| `kairos health --full` | 全量健康检查（含 P6 余量/审计链完整性/偏置监测状态） |

### 1.3 日志查看

```bash
kairos logs --level info           # 查看 info 及以上级别日志
kairos logs --module forgetting     # 仅查看遗忘模块日志
kairos logs --since "2 hours ago"  # 近 2 小时日志
kairos logs --follow                # 实时追踪（轻量模式）
```

标准模式下通过 `docker compose logs` 查看。

---

## §2 备份与恢复

### 2.1 数据库备份

| 模式 | 备份命令 | 恢复命令 |
|:----|:---------|:---------|
| 轻量模式 | `kairos db backup`（默认路径 `~/.kairos/backups/`） | 复制备份文件至 `~/.kairos/kairos.db` |
| 标准模式 | `pg_dump -h localhost -U kairos kairos > backup.sql` | `psql -h localhost -U kairos kairos < backup.sql` |

### 2.2 配置备份

```bash
# 备份完整配置和密钥
cp ~/.kairos/.env ~/.kairos/.env.bak    # 备份环境配置（见 deployment.md §三）
```

### 2.3 恢复验证

恢复后执行 `kairos health --full` 确认以下项正常：
- 数据库连接
- 审计链 HMAC 完整性
- 安全红线检查（S-01~S-19）

---

## §3 升级与降级

### 3.1 轻量模式

```bash
# 升级
pip install --upgrade kairos
kairos db migrate       # 执行数据库迁移

# 降级（需保留旧版本 wheel）
pip install kairos==<旧版本>
kairos db migrate rollback      # 回滚迁移
```

### 3.2 标准模式

```bash
# 升级
docker compose pull
docker compose up -d
kairos db migrate

# 降级
docker compose down
# 加载旧镜像版本（替换 Image tag 为目标版本后执行）
docker compose pull
docker compose up -d
kairos db migrate rollback
```

升级前建议先备份数据库。

---

## §4 配置与密钥管理

### 4.1 配置查看修改

| 操作 | 命令 |
|:----|:-----|
| 查看当前配置 | `kairos config show` |
| 修改单个参数 | `kairos config set KAIROS_DAILY_BUDGET_FEN 20000` |
| 重置为默认值 | `kairos config reset KAIROS_WM_SLOT_CAPACITY` |
| 配置生效 | 重启服务生效（配置文档 `configuration.md` §二 详述生效规则） |

### 4.2 API Key 管理

| 操作 | 命令 |
|:----|:-----|
| 生成 | `kairos init --init-key` |
| 轮换 | `kairos admin key rotate` |
| 吊销 | `kairos admin key revoke <key-id>` |

### 4.3 审计密钥轮换

```bash
kairos admin key rotate --hmac    # 轮换审计 HMAC 密钥
# 轮换时保留旧密钥校验历史记录，新记录使用新密钥签名
```

---

## §5 故障排查

### 5.1 启动失败

| 现象 | 检查项 |
|:-----|:-------|
| 拒绝启动 | ① `KAIROS_API_KEY` 是否设置 ② `KAIROS_SALT` 是否设置 |
| 数据库连接失败 | ① `KAIROS_DB_DSN` 是否正确 ② 数据库服务是否运行 |
| 端口冲突 | `--port` 参数指定可用端口 |

### 5.2 运行时异常

| 现象 | 排查步骤 |
|:-----|:---------|
| 写入过慢 | ① `kairos status` 检查注意力预算 ② 检查是否触发限流（S-02） |
| 检索无结果 | ① 确认路径前缀正确 ② 检查遗忘调度器是否过频 ③ 检查升华状态 |
| 校准信号无响应 | ① 检查外部校准端点可达性 ② `kairos health` 检查宪法主权面状态 |
| 告警持续 | ① `kairos logs --level warn` 定位源 ② 检查对应监测器阈值 ③ 按需调整参数 |

### 5.3 错误码索引

| 错误码 | 说明 | 处理 |
|:-------|:-----|:-----|
| `ERR-AUTH-001` | API Key 无效 | 检查 `KAIROS_API_KEY` 和 `KAIROS_SALT` |
| `ERR-AUTH-002` | API Key 过期/吊销 | 生成新 Key |
| `ERR-AUTH-003` | 权限不足 | 升级 Key 级别 |
| `ERR-RATE-001` | 写限流 | 等待重置或提高 `KAIROS_RATE_LIMIT_WRITE_PER_MIN` |
| `ERR-RATE-002` | 读限流 | 等待重置或提高 `KAIROS_RATE_LIMIT_READ_PER_MIN` |
| `ERR-INPUT-001` | 输入超长 | 减少内容长度 |
| `ERR-INPUT-002` | 路径格式无效 | 确认以 `kairos://` 开头 |
| `ERR-DB-001` | 数据库连接失败 | 检查 `KAIROS_DB_DSN` 和数据库服务 |
| `ERR-LLM-001` | LLM 调用超时 | 检查 LLM 端点可达性 |
| `ERR-SEC-001` | 安全红线违反 | 检查操作是否符合红线约束 |

完整错误码参考见 `references/error-reference.md`。

---

## §6 维护与审计

### 6.1 定期维护

| 周期 | 操作 | 命令 |
|:----|:-----|:-----|
| 日 | 健康检查 | `kairos health` |
| 周 | 审计链完整性检查 | `kairos audit verify-chain` |
| 月 | 数据库 VACUUM | `kairos db vacuum`（SQLite 模式）；PG 自动 VACUUM |
| 月 | 重构建索引 | `kairos db reindex` |
| 季度 | 安全红线复验 | 逐条执行 test-strategy §2.2 验收方法 |
| 季度 | 密钥轮换 | `kairos admin key rotate` |
| 季度 | HMAC 密钥轮换 | `kairos admin key rotate --hmac` |

### 6.2 审计操作

| 操作 | 命令 |
|:----|:-----|
| 查看审计日志 | `kairos audit log` |
| 验证审计链完整性 | `kairos audit verify-chain` |
| 定向遗忘审批 | `kairos audit approve-forgetting <id>` |

### 6.3 升华管道管理

| 操作 | 命令 |
|:----|:-----|
| 查看升华状态 | `kairos status --sublimation` |
| 触发升华轮次 | `kairos sublimation trigger` |
| 查看升华进度 | `kairos sublimation progress` |

### 6.4 证伪响应

当系统触发核心命题证伪或轴耦合证伪时：
1. `kairos status` 确认证伪信号类型
2. `kairos audit log` 查看证伪信号负载
3. 按架构 §10.10 证伪响应路径处理
4. 输出审查报告

---

## 版本记录

| 版本 | 日期 | 变更 |
|:----|:----|:-----|
| v1.0.0 | 2026-07-21 | 初始版本。日常操作/备份/升级/配置/故障/维护 |
