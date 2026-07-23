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
status: draft
---

# Kairos 开发环境搭建

> **状态声明**：本文描述的命令（`git clone` → `uv pip install -e ".[dev]"` → `kairos init` → `kairos serve`）为**设计目标**。当前代码（`amber/`）为先行实验性实现，无 pyproject.toml，依赖通过 `pip install -r amber/requirements.txt` 安装。实际入口为 `python amber/main.py`（FastAPI）。本文待 CLI 构建后重写。

> **定位**：开发者从零开始搭建 Kairos 开发环境。
>
> **⚠ 草稿完善声明**：以下所有命令为架构设计阶段的目标示例。项目当前处于草稿完善阶段期（见 changelog），CLI 尚未构建（当前代码入口为 `python amber/main.py`）。命令格式和参数将在代码启动后最终确认。

---

## 一、前置条件

| 依赖 | 版本 | 验证命令 |
|:----|:----|:---------|
| Python | ≥ 3.11 | `python --version` |
| uv | ≥ 0.4 | `uv --version` |
| Git | ≥ 2.40 | `git --version` |
| Docker | ≥ 24.0（标准模式需要） | `docker --version` |
| BGE-M3 嵌入模型 | 轻量模式本地运行需要 | 自动下载（首次 `kairos serve` 时） |

## 二、克隆与虚拟环境

```bash
git clone https://github.com/JohnL1989/kairos.git
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

# 1. 初始化密钥（自动生成全部四个密钥并写入环境文件）
kairos init --init-key

# 2. 初始化数据库（密钥已就绪，自动加载）
kairos init --db sqlite:///data/kairos-dev.db

# 标准模式（需要 Docker PostgreSQL）
docker run -d --name kairos-pg -p 5432:5432 \
  -e POSTGRES_PASSWORD=kairos pgvector/pgvector:pg15
kairos init --db postgresql://postgres:***@localhost:5432/kairos
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
