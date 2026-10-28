$ErrorActionPreference = 'Continue'
$Root = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $Root '.tmp\runlogs'
$PidFile = Join-Path $LogDir 'pids.json'

$ports = @(
    @{ Name = 'MainFrontend';   Port = 5173 },
    @{ Name = 'AgentFrontend';  Port = 5374 },
    @{ Name = 'CookieBridge';   Port = 8274 },
    @{ Name = 'AgentBackend';   Port = 8002 },
    @{ Name = 'CrawlerEngine';  Port = 8005 },
    @{ Name = 'DownloadServer'; Port = 8205 },
    @{ Name = 'SignService';    Port = 8989 },
    @{ Name = 'MainBackend';    Port = 8000 }
)

function Stop-Port {
    param([int]$Port)
    $conns = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    if (-not $conns) { return $false }
    $stopped = $false
    foreach ($c in $conns) {
        try {
            Stop-Process -Id $c.OwningProcess -Force -ErrorAction Stop
            $stopped = $true
        } catch {
            Write-Host ('  [WARN] pid {0} stop failed: {1}' -f $c.OwningProcess, $_.Exception.Message) -ForegroundColor Yellow
        }
    }
    return $stopped
}

Write-Host ''
Write-Host '=============================================' -ForegroundColor Cyan
Write-Host ' AI-Content-Automation STOP ALL' -ForegroundColor Cyan
Write-Host '=============================================' -ForegroundColor Cyan
Write-Host ''

foreach ($item in $ports) {
    $wasRunning = [bool](Get-NetTCPConnection -State Listen -LocalPort $item.Port -ErrorAction SilentlyContinue)
    if (-not $wasRunning) {
        Write-Host ('  [SKIP] {0,-16} :{1} not running' -f $item.Name, $item.Port) -ForegroundColor DarkGray
        continue
    }
    if (Stop-Port -Port $item.Port) {
        Write-Host ('  [OK]   {0,-16} :{1} stopped' -f $item.Name, $item.Port) -ForegroundColor Green
    } else {
        Write-Host ('  [FAIL] {0,-16} :{1} stop failed' -f $item.Name, $item.Port) -ForegroundColor Red
    }
}

Write-Host ''
Write-Host '[Infra kept running] MySQL 3306 / Redis 6379 / MinIO 9000' -ForegroundColor DarkGray
Write-Host ''

$remaining = @()
foreach ($item in $ports) {
    if (Get-NetTCPConnection -State Listen -LocalPort $item.Port -ErrorAction SilentlyContinue) {
        $remaining += ('{0}:{1}' -f $item.Name, $item.Port)
    }
}

if ($remaining.Count -gt 0) {
    Write-Host ('Still listening: {0}' -f ($remaining -join ', ')) -ForegroundColor Yellow
    exit 1
}

if (Test-Path -LiteralPath $PidFile) { Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue }
Write-Host 'All project services stopped.' -ForegroundColor Green
Write-Host ''
exit 0
