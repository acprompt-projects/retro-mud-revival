# Retro MUD Revival - 一键启动脚本
# 同时启动 Telnet 服务器 + WebSocket 桥接器 + 打开浏览器

$serverJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    python server.py
} -Name "MUD-Telnet"

Start-Sleep -Seconds 2

$bridgeJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    python websocket_bridge.py
} -Name "MUD-WebSocket"

Start-Sleep -Seconds 2

Write-Host "🏰 Retro MUD Revival 正在启动..." -ForegroundColor Green
Write-Host "Telnet 服务器: localhost:4000" -ForegroundColor Cyan
Write-Host "WebSocket 桥接: ws://localhost:8080" -ForegroundColor Cyan
Write-Host "Web 客户端: web/index.html" -ForegroundColor Cyan
Write-Host ""
Write-Host "按 Ctrl+C 停止所有服务" -ForegroundColor Yellow

# 打开浏览器
$webPath = Join-Path $PWD "web\index.html"
Start-Process "explorer.exe" $webPath

# 保持运行直到用户按 Ctrl+C
try {
    while ($true) {
        Start-Sleep -Seconds 5
        $telnetRunning = Get-NetTCPConnection -LocalPort 4000 -ErrorAction SilentlyContinue
        $wsRunning = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue
        if (-not $telnetRunning) {
            Write-Host "[!] Telnet 服务器已停止" -ForegroundColor Red
        }
        if (-not $wsRunning) {
            Write-Host "[!] WebSocket 桥接器已停止" -ForegroundColor Red
        }
    }
} finally {
    Write-Host "正在停止服务..." -ForegroundColor Yellow
    Stop-Job -Name "MUD-Telnet" -ErrorAction SilentlyContinue
    Stop-Job -Name "MUD-WebSocket" -ErrorAction SilentlyContinue
    Remove-Job -Name "MUD-Telnet" -ErrorAction SilentlyContinue
    Remove-Job -Name "MUD-WebSocket" -ErrorAction SilentlyContinue
    Write-Host "已清理" -ForegroundColor Green
}
