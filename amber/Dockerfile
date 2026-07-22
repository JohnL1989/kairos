FROM python:3.11-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# 应用代码：把 amber/ 子目录内容直接复制到 /app/ 根目录
# 复制后：/app/main.py, /app/api/, /app/core/, /app/migrations/ 等
COPY . .

# Python 依赖（COPY . . 后安装）
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# 非 root 用户运行
RUN groupadd -r amber && useradd -r -g amber -d /app -s /sbin/nologin amber && \
    chown -R amber:amber /app
USER amber

EXPOSE 8010

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8010/api/v1/health/default')" || exit 1

# 路径：/app/main.py（flat 结构），import 直接是 api.response、core.xxx
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]
