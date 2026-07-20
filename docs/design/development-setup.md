---
title: Kairos 开发环境搭建
aliases:
  - 开发环境
  - Development Setup
tags:
  - kairos
  - development
  - setup
created: 2026-07-20
updated: 2026-07-20
status: v1.0.0
---

# Kairos 开发环境搭建

> **定位**：本地开发环境搭建步骤。deployment.md 面向运行环境，本文面向开发环境。

---

## 一、前置条件

| 依赖 | 版本 | 验证命令 |
|:----|:----|:---------|
| Python | ≥ 3.11 | `python --version` |
| uv | ≥ 0.4 | `uv --version` |
| Git | ≥ 2.40 | `git --version` |
| Docker | ≥ 24.0（标准模式需要） | `docker --version` |

## 二、克隆与虚拟环境

```bash
git clone https://github.com/JohnL1989/Aion-Memory.git kairos
cd kairos

# 创建虚拟环境
uv venv
source .venv/bin/activate   # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
uv pip install -e ".[dev]"

# 安装 pre-commit hooks
pre-commit install
```

## 三、数据库初始化

```bash
# 轻量模式（推荐开发使用）
kairos init --db sqlite:///data/kairos-dev.db

# 标准模式（需要 Docker PostgreSQL）
docker run -d --name kairos-pg -p 5432:5432 \
  -e POSTGRES_PASSWORD=kairos pgvector/pgvector:pg15
kairos init --db postgresql://postgres:kairos@localhost:5432/kairos
```

## 四、运行测试

```bash
# 单元测试
pytest tests/unit/ -v --cov=src

# 集成测试（需要 Docker）
pytest tests/integration/ -v

# E2E 测试（需要 Docker）
pytest tests/e2e/ -v

# 全部测试
pytest -v
```

## 五、常用命令

```bash
# 类型检查
mypy src/

# 代码格式检查
ruff check src/ tests/

# 代码格式化
ruff format src/ tests/

# 启动开发服务器（热重载）
kairos serve --port 8010 --reload
```

## 六、IDE 配置建议

### VS Code

推荐扩展：
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Ruff (charliermarsh.ruff)
- GitHub Copilot

`settings.json` 建议：
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.analysis.typeCheckingMode": "basic",
  "ruff.lint.enable": true,
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "charliermarsh.ruff",
  "files.exclude": {
    "**/.venv": true,
    "**/__pycache__": true
  }
}
```

---

## 版本记录

| 版本 | 日期 | 变更 |
|:----|:----|:-----|
| v1.0.0 | 2026-07-20 | 初始开发环境搭建指南。 |
