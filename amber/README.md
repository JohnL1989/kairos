# Amber — 记忆蒸馏引擎

Amber 是 Aion Memory 的记忆蒸馏核心，提供：

- **TMT 多层蒸馏**：L1 碎片 → L2 会话 → L3 日报 → L4 周报
- **语义检索**：5D 搜索 + 关键词降级
- **记忆反思**：热度衰减 + 冗余合
- **用户画像**：信念系统自动提炼

## 构建

```bash
docker build -t amber-api ./amber
```

## 配置

通过环境变量配置（参考 `templates/amber.env.example`）：

| 变量 | 说明 | 默认 |
|------|------|------|
| `LLM_API_KEY` | LLM API key | — |
| `LLM_BASE_URL` | LLM API base URL | `https://api.deepseek.com/v1` |
| `LLM_MODEL_MINI` | 轻量模型 | `deepseek-chat` |
| `EMBEDDING_ENDPOINT` | 嵌入 API（可选，默认 FTS5 降级） | — |

## 目录结构

```
amber/
├── Dockerfile           # 构建文件
├── requirements.txt     # Python 依赖
├── main.py              # FastAPI 入口（210 行，v1.7.0）
├── config.py            # 配置模块（环境变量驱动）
├── schema.sql           # PostgreSQL schema（v1.7.0 对齐代码）
│
├── api/                 # API 路由（12 模块）
│   ├── memories.py      # 记忆 CRUD
│   ├── beliefs.py       # 信念管理
│   ├── search.py        # 语义检索 + 辩证搜索（两阶段）
│   ├── chunks.py        # RAG 分块搜索
│   ├── sessions.py      # 会话归档
│   ├── media.py         # 多模态记忆
│   ├── wiki.py          # Wiki 知识库
│   ├── projects.py      # 项目沙箱
│   ├── tools.py         # 工具归档
│   ├── security.py      # 安全控制（审计/净化/化石）
│   ├── shared.py        # 依赖注入（pool, embedding_fn, get_current_user）
│   └── response.py      # 统一响应信封（code/message/data）
│
├── services/            # 服务层（v1.5.0+）
│   └── memory_service.py  # 业务逻辑：热度衰减、层级迁移、冲突检测
│
├── tmt/                 # TMT 蒸馏引擎
│   └── router.py        # 蒸馏 API 端点 + 聚类与合并
│
├── core/                # 核心引擎
│   ├── embedding.py     # 嵌入抽象层（内置缓存，零向量容错）
│   ├── chunker.py       # 记忆分块（事务包裹）
│   └── llm.py           # LLM 调用封装（分级重试+成本统计）
│
├── security/            # 安全层
│   ├── audit.py         # 双采样一致性检查
│   └── purifier.py      # 哈希净化与化石节点
│
├── migrations/          # 数据库迁移（v1.5.0+）
│   └── 0001_schema_v1.5.0.sql
│
└── integrations/        # 第三方集成
    └── sdk.py           # Hermes MemoryProvider SDK
```
