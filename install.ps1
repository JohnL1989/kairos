# Aion Memory — Windows 安装脚本 (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Aion Memory — 安装开始" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$AionHome = "$env:USERPROFILE\.aion-memory"
$HermesHome = "$env:LOCALAPPDATA\hermes"

# 1. 创建配置目录
New-Item -ItemType Directory -Force -Path "$AionHome\scripts" | Out-Null
New-Item -ItemType Directory -Force -Path "$AionHome\logs" | Out-Null
Write-Host "✅ 配置目录: $AionHome" -ForegroundColor Green

# 2. 复制脚本
Copy-Item -Path "scripts\*.py" -Destination "$AionHome\scripts\" -Force
Write-Host "✅ 脚本已安装" -ForegroundColor Green

# 3. 安装 Python 依赖
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python 依赖已安装" -ForegroundColor Green
}

# 4. 安装 Hermes MemoryProvider 插件
if (Test-Path "$HermesHome\plugins") {
    New-Item -ItemType Directory -Force -Path "$HermesHome\plugins\aion-memory" | Out-Null
    Copy-Item -Path "adapters\*.py" -Destination "$HermesHome\plugins\aion-memory\" -Force
    Copy-Item -Path "plugin.yaml" -Destination "$HermesHome\plugins\aion-memory\" -Force
    Write-Host "✅ Hermes MemoryProvider 插件已安装" -ForegroundColor Green
    Write-Host "   执行以下命令激活：" -ForegroundColor Green
    Write-Host "   hermes config set memory.provider aion-memory" -ForegroundColor Green
    Write-Host "   hermes reload" -ForegroundColor Green
} else {
    Write-Host "⚠️ 未找到 Hermes 插件目录，跳过插件安装" -ForegroundColor Yellow
}

# 5. 复制 Hermes Skills
if (Test-Path "$HermesHome\skills") {
    Copy-Item -Path "skills\*" -Destination "$HermesHome\skills\" -Recurse -Force
    Write-Host "✅ Hermes Skills 已安装" -ForegroundColor Green
} else {
    Write-Host "⚠️ 未找到 Hermes 目录，跳过技能安装" -ForegroundColor Yellow
}

# 6. 复制配置模板
if (-not (Test-Path "$AionHome\config.yaml")) {
    Copy-Item "templates\aion-config.yaml.example" "$AionHome\config.yaml"
    Write-Host "✅ 默认配置已创建" -ForegroundColor Green
}

# 6. 注册开机自启
$regPath = "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
$existing = Get-ItemProperty -Path $regPath -Name "AionMemory" -ErrorAction SilentlyContinue
if (-not $existing) {
    $pythonw = (Get-Command pythonw).Source
    Set-ItemProperty -Path $regPath -Name "AionMemory" -Value "`"$pythonw`" `"$AionHome\scripts\aion-startup.py`""
    Write-Host "✅ 开机自启已注册" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✅ Aion Memory 安装完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步："
Write-Host "  1. cd templates; copy honcho.env.example honcho.env"
Write-Host "  2. 编辑 honcho.env 填入你的 API key"
Write-Host "  3. docker compose -f docker-compose.yml.example up -d"
Write-Host "  4. hermes config set memory.provider aion-memory"
Write-Host "  5. hermes reload"
