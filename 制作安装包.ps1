# AI Tutor 安装包制作脚本
$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   AI Tutor 安装包制作工具" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$projectDir = $PSScriptRoot
$packageName = "AI-Tutor-安装包"
$packageDir = Join-Path $projectDir $packageName
$zipName = "AI-Tutor-计算机设计大赛.zip"

Write-Host "[1/5] 清理旧文件..." -ForegroundColor Yellow
if (Test-Path $packageDir) {
    Remove-Item -Recurse -Force $packageDir
}
if (Test-Path (Join-Path $projectDir $zipName)) {
    Remove-Item -Force (Join-Path $projectDir $zipName)
}

Write-Host "[2/5] 创建安装包目录..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $packageDir | Out-Null
New-Item -ItemType Directory -Path "$packageDir\backend" | Out-Null
New-Item -ItemType Directory -Path "$packageDir\frontend" | Out-Null
New-Item -ItemType Directory -Path "$packageDir\docs" | Out-Null

Write-Host "[3/5] 复制后端代码..." -ForegroundColor Yellow
$backendDirs = @("agent", "api", "database", "kg", "multimodal", "rag", "services", "utils")
foreach ($dir in $backendDirs) {
    $source = Join-Path $projectDir "backend\$dir"
    $dest = Join-Path $packageDir "backend\$dir"
    if (Test-Path $source) {
        Copy-Item -Recurse $source $dest
        Write-Host "  - 复制 backend\$dir" -ForegroundColor Gray
    }
}

$backendFiles = @("main.py", "start.py", "requirements.txt")
foreach ($file in $backendFiles) {
    $source = Join-Path $projectDir "backend\$file"
    $dest = Join-Path $packageDir "backend\$file"
    if (Test-Path $source) {
        Copy-Item $source $dest
        Write-Host "  - 复制 backend\$file" -ForegroundColor Gray
    }
}

# 复制 .env 为示例文件
$envSource = Join-Path $projectDir "backend\.env"
$envDest = Join-Path $packageDir "backend\.env.example"
if (Test-Path $envSource) {
    Copy-Item $envSource $envDest
    Write-Host "  - 复制 backend\.env.example" -ForegroundColor Gray
}

Write-Host "[4/5] 复制前端代码..." -ForegroundColor Yellow
$frontendDirs = @("src", "public")
foreach ($dir in $frontendDirs) {
    $source = Join-Path $projectDir "frontend\$dir"
    $dest = Join-Path $packageDir "frontend\$dir"
    if (Test-Path $source) {
        Copy-Item -Recurse $source $dest
        Write-Host "  - 复制 frontend\$dir" -ForegroundColor Gray
    }
}

$frontendFiles = @("package.json", "vite.config.js", "index.html")
foreach ($file in $frontendFiles) {
    $source = Join-Path $projectDir "frontend\$file"
    $dest = Join-Path $packageDir "frontend\$file"
    if (Test-Path $source) {
        Copy-Item $source $dest
        Write-Host "  - 复制 frontend\$file" -ForegroundColor Gray
    }
}

Write-Host "[5/5] 复制文档和启动脚本..." -ForegroundColor Yellow
$docFiles = @("README.md", "安装包说明.md", "SETUP.md", "一键启动.bat")
foreach ($file in $docFiles) {
    $source = Join-Path $projectDir $file
    if (Test-Path $source) {
        if ($file -eq "SETUP.md") {
            Copy-Item $source (Join-Path $packageDir "docs\$file")
        } else {
            Copy-Item $source $packageDir
        }
        Write-Host "  - 复制 $file" -ForegroundColor Gray
    }
}

Write-Host "打包压缩..." -ForegroundColor Yellow
$zipPath = Join-Path $projectDir $zipName
Compress-Archive -Path $packageDir -DestinationPath $zipPath -Force

# 显示结果
$zipFile = Get-ChildItem $zipPath
$sizeMB = [math]::Round($zipFile.Length / 1MB, 2)

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  安装包制作完成！" -ForegroundColor Green
Write-Host "  文件名: $zipName" -ForegroundColor Green
Write-Host "  大小: $sizeMB MB" -ForegroundColor Green
Write-Host "  路径: $zipPath" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# 清理临时目录
Remove-Item -Recurse -Force $packageDir

Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
