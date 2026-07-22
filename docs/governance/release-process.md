---
title: Kairos 发布流程
aliases:
  - 发布管理
  - release-process
tags:
  - kairos
  - governance
  - release
created: 2026-07-21
updated: 2026-07-21
status: draft
---

# Kairos 发布流程

> **定位**：第一次发布前定义版本号规则、发布检查清单、发布步骤、发布说明模板。防止每次发布都是临时起意。
>
> **单人简化**：发布流程可一人走完。CI 辅助，但核心步骤人工检查不省略。

---

## §1 版本号规则

遵循 SemVer 2.0：`MAJOR.MINOR.PATCH`

| 版本 | 何时递增 | 示例 |
|:----|:---------|:-----|
| **MAJOR** | 破坏性架构变更 / API 不兼容 / 数据库 schema 不兼容 | v1.0.0 → v2.0.0 |
| **MINOR** | 新功能（向后兼容）/ 降级 / 废弃 | v1.0.0 → v1.1.0 |
| **PATCH** | Bug 修复 / 性能优化 / 文档更新（无功能变化） | v1.0.0 → v1.0.1 |

**v1.0.0 特殊规则**：v1.0.0 = 设计冻结版（当前版本）。代码首版（首次可运行）从 v1.0.1 起——设计冻结与代码发布在版本号上明确分离。

---

## §2 发布检查清单

每次发布前逐项检查（单人可在一小时内走完）：

- [ ] 所有 P0 bug 已修复
- [ ] 单元测试覆盖率 ≥80%
- [ ] 6 条 E2E 全部通过
- [ ] 19 条安全红线（S-01~S-19）逐条验证通过
- [ ] `CHANGELOG.md` 已更新（新功能/修复/破坏性变更/已知问题）
- [ ] 版本号已在 `__init__.py` 中更新
- [ ] 文档交叉引用一致性检查通过
- [ ] 数据库迁移脚本可回滚（`kairos db migrate` + `kairos db rollback` 均正常）
- [ ] 备份已创建
- [ ] 构建产物正常（`uv build` 无错误）

---

## §3 发布步骤

> **⚠ 代码启动前不可执行**：以下步骤假定 Kairos 已有可运行的代码包。当前项目处于设计冻结阶段，代码尚未启动。此文档保留发布流程框架供参考，实际执行须在代码启动后重新校准确认。

```bash
# 1. 检查清单 → 全过
# 2. 构建
uv build

# 3. 测试安装
uv pip install dist/kairos-*.whl
kairos --version     # 确认版本号正确
kairos health        # 确认服务正常

# 4. 提交 + Tag
git add .
git commit -m "release: v1.0.1"
git tag v1.0.1
git push origin main --tags

# 5. GitHub Release
gh release create v1.0.1 \
  --title "v1.0.1" \
  --notes "见 CHANGELOG.md" \
  dist/kairos-*.whl dist/kairos-*.tar.gz

# 6. 发布后验证
pip install kairos==1.0.1
kairos init --seed-path ~/.kairos/seeds.yaml
kairos health --full
```

---

## §4 发布说明模板

```markdown
## vX.Y.Z - YYYY-MM-DD

### 新功能
- （列出新增功能及对应 Issue/PR）

### Bug 修复
- （列出修复的 bug 及对应 Issue）

### 破坏性变更
- （如有，列出变更内容 + 迁移指南链接）

### 已知问题
- （如有，列出未修复已知问题）

### 升级注意事项
- （如有，列出需要手动操作的步骤）
```

---

## §5 API 版本化与弃用

| 策略 | 规则 |
|:----|:-----|
| **版本化** | API 前缀 `/v1/`、`/v2/`，支持跨版本共存 |
| **弃用通知** | 废弃端点在 Header 返回 `Deprecation: true` + `Sunset: <date>` |
| **最低支持周期** | 弃用后至少支持 2 个 MINOR 版本 |
| **迁移指南** | 每次破坏性变更发布时附带迁移说明 |

---

## §6 许可证

| 项 | 内容 |
|:---|:-----|
| 项目许可证 | MIT（代码）+ CC-BY-4.0（文档） |
| 第三方依赖 | 所有依赖不引入 GPL/AGPL（兼容 MIT） |
| 依赖合规 | 每次 `uv sync` 后运行 `uv licenses` 检查许可兼容性 |

---

## §7 隐私声明（简要）

Kairos 存储的记忆数据默认仅存储在本地。收集的数据类型、保留策略、删除方法详见 `security/security-specification.md §4` 隐私评估。

---

## 版本记录

| 版本 | 日期 | 变更 |
|:----|:----|:-----|
| v1.0.0 | 2026-07-21 | 初始版本。版本号规则/检查清单/发布步骤/发布说明/API 弃用/许可证/隐私 |
