---
title: Kairos 故障排查指南
aliases:
  - 故障排查
  - Troubleshooting
tags:
  - kairos
  - ops
  - troubleshooting
created: 2026-07-18
updated: 2026-07-21
status: draft
---

# Kairos 故障排查指南

> **文档定位：** 常见问题的排查步骤和恢复命令。不包含系统设计或配置细节——部署配置见 `docs/ops/deployment.md`，可靠性策略见 `docs/ops/reliability.md`，设计约束见 `docs/foundation/architecture-v1.0.0.md` §7「安全红线」。

---

| 症状 | 排查步骤 | 恢复命令 |
|:----|:--------|:--------|
| **Kairos 无法启动** | ① 检查 `KAIROS_SALT` 是否设置 ② 检查 `KAIROS_DB_DSN` 是否正确 ③ 检查数据库是否可连接 | 设置环境变量后重启容器 |
| **按需召回返回空** | ① 检查嵌入模型是否在线 ② 检查 memories 表是否有数据 ③ 检查是否为短查询被门禁拦截 | 嵌入恢复后自动重试 |
| **常驻契约不更新** | ① 检查冻结快照机制——写入已落盘但当前 session 不刷新 ② 新 session 是否加载了新内容 | 新 session 自动生效 |
| **升华层不运行** | ① 检查调度器状态 ② 检查系统是否持续处于「推理活跃」状态 ③ 检查 events 表中升华阶段的状态 | 推理空闲后自动触发 |
| **磁盘使用率超 85%** | ① 检查 archive 目录大小 ② 检查备份目录大小 | 手动清理过期备份或触发升华层激进归档 |
| **契约分配错误** | ① 检查写入时是否指定了 contract 参数 ② 一键模式默认分配按需契约 | 显式指定 contract 参数重试 |
| **路径搜索结果跨路径** | ① 检查 SQL 中 path 前缀过滤是否正确 ② 检查索引状态 | 重建索引或修复查询条件 |
| **升华阶段停滞** | ① 检查 events 表中对应阶段的状态 ② 检查调度器是否处于空闲状态 | 重启调度器或手动插入下一阶段事件：`INSERT INTO sublimation_events (memory_id, stage, status) VALUES ('uuid', 'L2', 'pending');` |
| **错误码索引** | ① 检查日志中的 `error_code` 字段 ② 按 `ERR-` 前缀检索以下索引 |
| `ERR-AUTH-001` | API Key 无效或未设置 | 检查 `KAIROS_API_KEY` 和 `KAIROS_SALT` 环境变量 |
| `ERR-AUTH-002` | API Key 已过期/被吊销 | 检查 API Key 有效期，生成新 Key |
| `ERR-AUTH-003` | 权限不足 | 升级 API Key 级别 |
| `ERR-RATE-001` | 写操作限流 | 等待限流窗口重置或调高 `KAIROS_RATE_LIMIT_WRITE_PER_MIN` |
| `ERR-RATE-002` | 读操作限流 | 等待限流窗口重置或调高 `KAIROS_RATE_LIMIT_READ_PER_MIN` |
| `ERR-INPUT-001` | 输入超长 | 减少 content/query 长度或调大限制值 |
| `ERR-INPUT-002` | 路径格式无效（非 `kairos://` 开头） | 确认路径以 `kairos://` 开头 |
| `ERR-DB-001` | 数据库连接失败 | 检查 `KAIROS_DB_DSN` 和数据库运行状态 |
| `ERR-DB-002` | 数据库迁移失败 | 检查迁移文件完整性或回滚至上个版本 |
| `ERR-LLM-001` | LLM 调用超时 | 检查 LLM 供应商端点和网络连通性 |
| `ERR-LLM-002` | LLM 日预算耗尽 | 等待预算重置或调高 `KAIROS_DAILY_BUDGET_FEN` |
| `ERR-SEC-001` | 安全红线违反（详情见审计日志） | 检查操作是否符合红线约束，查看审计日志 |
| **安全事件排查** | | |
| **API Key 疑似泄露** | ① 立即吊销泄露 Key ② 生成新 Key 并更新 `KAIROS_API_KEY` ③ 检查审计日志中该 Key 在泄露时间窗口内的所有操作 | `kairos admin key rotate` |
| **数据库文件损坏** | ① 停止服务 ② 从最近备份恢复 ③ 运行 `kairos db verify` ④ 如备份不可用，尝试 `kairos db repair` | `kairos db restore <backup_path>` |
| **升级失败回滚** | ① 停止服务 ② 恢复旧版本二进制/镜像 ③ 执行 `kairos db migrate rollback` 回滚数据库迁移 | 旧镜像版本 + `docker compose up -d` |
