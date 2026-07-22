#!/bin/bash
# Aion Memory — Linux/macOS 安装脚本

set -e

echo "========================================"
echo "  Aion Memory — 安装开始"
echo "========================================"

AION_HOME="${AION_HOME:-$HOME/.aion-memory}"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"

# 1. 创建配置目录
mkdir -p "$AION_HOME"/{scripts,logs}
echo "✅ 配置目录: $AION_HOME"

# 2. 复制脚本
cp -r scripts/*.py "$AION_HOME/scripts/"
chmod +x "$AION_HOME/scripts/"*.py
echo "✅ 脚本已安装"

# 3. 安装 Python 依赖
pip install -r requirements.txt 2>/dev/null || pip3 install -r requirements.txt
echo "✅ Python 依赖已安装"

# 4. 安装 Hermes MemoryProvider 插件
if [ -d "$HERMES_HOME/plugins" ]; then
    mkdir -p "$HERMES_HOME/plugins/aion-memory"
    cp -r adapters/*.py "$HERMES_HOME/plugins/aion-memory/"
    cp plugin.yaml "$HERMES_HOME/plugins/aion-memory/"
    echo "✅ Hermes MemoryProvider 插件已安装"
    echo "   执行以下命令激活："
    echo "   hermes config set memory.provider aion-memory"
    echo "   hermes reload"
else
    echo "⚠️ 未找到 Hermes 插件目录 ($HERMES_HOME/plugins)，跳过插件安装"
fi

# 5. 复制 Hermes Skills
if [ -d "$HERMES_HOME/skills" ]; then
    mkdir -p "$HERMES_HOME/skills"
    cp -r skills/* "$HERMES_HOME/skills/"
    echo "✅ Hermes Skills 已安装"
else
    echo "⚠️ 未找到 Hermes 目录 ($HERMES_HOME)，跳过技能安装"
fi

# 6. 复制配置模板（不覆盖已有）
if [ ! -f "$AION_HOME/config.yaml" ]; then
    cp templates/aion-config.yaml.example "$AION_HOME/config.yaml"
    echo "✅ 默认配置已创建"
fi

# 6. 注册开机自启（systemd）
if command -v systemctl &>/dev/null; then
    cat > /tmp/aion-memory.service << EOF
[Unit]
Description=Aion Memory System
After=docker.service

[Service]
Type=oneshot
ExecStart=$(which python3) $AION_HOME/scripts/aion-startup.py
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
    sudo mv /tmp/aion-memory.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable aion-memory.service
    echo "✅ 开机自启已注册 (systemd)"
fi

echo ""
echo "========================================"
echo "  ✅ Aion Memory 安装完成"
echo "========================================"
echo ""
echo "下一步："
echo "  1. cd templates && cp honcho.env.example honcho.env"
echo "  2. 编辑 honcho.env 填入你的 API key"
echo "  3. docker compose -f docker-compose.yml.example up -d"
echo "  4. hermes config set memory.provider aion-memory"
echo "  5. hermes reload"
echo ""
