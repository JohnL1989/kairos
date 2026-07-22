#!/bin/bash
# Aion Memory — 数据库初始化入口（R10 修复：增量迁移）
# 首次部署：跑 schema.sql 建立完整 schema（含 schema_migrations 版本表）；
# 之后每次启动仅应用「未在 schema_migrations 登记」的迁移文件，不再重复执行
# schema.sql，从源头杜绝 schema.sql 与 migrations 双轨漂移（见审计报告 R10）。

set -e

# 从环境变量读取，兼容 amber.env.example 的旧名 AUTH_DISABLED
PG_DSN="${PG_DSN:-postgresql://postgres:***@amber-db:5432/amber}"

echo "🔍 [entrypoint] 等待数据库就绪..."

# 提取连接参数
PG_USER=$(echo "$PG_DSN" | sed -n 's|.*://\([^:]*\):.*|\1|p')
PG_PASS=$(echo "$PG_DSN" | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p')
PG_HOST=$(echo "$PG_DSN" | sed -n 's|.*@\([^:]*\):.*|\1|p')
PG_PORT=$(echo "$PG_DSN" | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
PG_DB=$(echo "$PG_DSN" | sed -n 's|.*/\([^?]*\)|\1|p')

# 导出独立变量供 config.py 使用（asyncpg create_pool 主要读 PG_DSN，
# PGPASSWORD 仅在 PG_DSN 未设置时作回退；此处不再导出明文密码，
# 避免 /proc/<pid>/environ、docker inspect、docker exec 可读到密码（S10 修复）。
# psql 认证统一走下方 .pgpass（PGPASSFILE），不依赖 PGPASSWORD 环境变量。
export PGUSER="$PG_USER"
export PGHOST="$PG_HOST"
export PGPORT="$PG_PORT"
export PGDATABASE="$PG_DB"

echo "🔧 [entrypoint] 数据库连接: $PGHOST:$PGPORT/$PGDATABASE (user=$PG_USER)"

# 创建临时 .pgpass 文件，避免密码暴露在进程命令行
PGPASSFILE=$(mktemp)
echo "$PG_HOST:$PG_PORT:$PG_DB:$PG_USER:$PG_PASS" > "$PGPASSFILE"
chmod 600 "$PGPASSFILE"
export PGPASSFILE

# 清理函数
cleanup() { rm -f "$PGPASSFILE"; }
trap cleanup EXIT

for i in $(seq 1 30); do
    if psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -c "SELECT 1" > /dev/null 2>&1; then
        echo "✅ [entrypoint] 数据库就绪"
        break
    fi
    echo "⏳ [entrypoint] 等待数据库 ($i/30)..."
    sleep 2
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCHEMA="$SCRIPT_DIR/schema.sql"
MIGRATIONS_DIR="$SCRIPT_DIR/migrations"

# 是否已 bootstrap：schema_migrations 表存在即视为已跑过 schema.sql，
# 不再重复执行（避免 R5 所述 ACCESS EXCLUSIVE 锁 + 全表重建，及双轨漂移）。
IS_BOOTSTRAPPED=$(psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -tAc \
    "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='schema_migrations'" 2>/dev/null)

if [ -z "$IS_BOOTSTRAPPED" ]; then
    echo "📦 [entrypoint] 全新库：执行 schema.sql（仅首次）..."
    psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -f "$SCHEMA" -q
    echo "✅ [entrypoint] schema.sql 完成"
else
    echo "⏭️  [entrypoint] schema_migrations 已存在，跳过 schema.sql（避免双轨漂移）"
fi

# 增量应用迁移：仅执行未在 schema_migrations 登记的迁移文件，并登记其名称。
if [ -d "$MIGRATIONS_DIR" ]; then
    APPLIED=$(psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -tAc \
        "SELECT migration_name FROM schema_migrations" 2>/dev/null | sed '/^$/d' | sort)
    for f in $(ls "$MIGRATIONS_DIR"/*.sql 2>/dev/null | sort); do
        name=$(basename "$f")
        if echo "$APPLIED" | grep -qx "$name"; then
            echo "⏭️  [entrypoint] 跳过已应用迁移 $name"
        else
            echo "📦 [entrypoint] 执行迁移 $name..."
            if psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -f "$f" -q && \
               psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -c \
                 "INSERT INTO schema_migrations(migration_name) VALUES ('$name') ON CONFLICT (migration_name) DO NOTHING" -q; then
                echo "✅ [entrypoint] $name 完成（已登记）"
            else
                echo "❌ [entrypoint] $name 执行失败，中止启动（避免 schema 部分应用的不一致状态）"
                exit 1
            fi
        fi
    done
fi

echo "🚀 [entrypoint] 启动 uvicorn..."
# 路径结构：/app/main.py（COPY amber/ 后平铺到 /app/）
exec python -m uvicorn main:app --host 0.0.0.0 --port 8010
