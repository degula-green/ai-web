param(
    [switch]$SkipFrontend,
    [switch]$SkipCrawler,
    [switch]$SkipCookieBridge
)

$ErrorActionPreference = 'Continue'
$Root = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $Root '.tmp\runlogs'
$PidFile = Join-Path $LogDir 'pids.json'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Test-Port {
    param([int]$Port)
    return [bool](Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
}

function Test-Health {
    param([string]$Url, [int]$TimeoutSec = 3)
    if (-not $Url) { return $true }
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec
        return ($r.StatusCode -ge 200 -and $r.StatusCode -lt 400)
    } catch {
        return $false
    }
}

function Wait-Health {
    param([string]$Url, [int]$Seconds)
    for ($i = 0; $i -lt $Seconds; $i++) {
        if (Test-Health -Url $Url) { return $true }
        Start-Sleep -Seconds 1
    }
    return (Test-Health -Url $Url)
}

$uv = (Get-Command uv -ErrorAction SilentlyContinue).Source
if (-not $uv) { $uv = 'D:\python\uv\bin\uv.exe' }
$cmdExe = 'C:\Windows\System32\cmd.exe'
$nodeDir = 'C:\Program Files\nodejs'

$downloadPython = Join-Path $Root 'backend\agent-stack\download-service\DownloadServer\.venv\Scripts\python.exe'
$crawlerPython = Join-Path $Root 'backend\agent-stack\crawler-engine\.venv\Scripts\python.exe'

$services = @()

function New-Svc($key, $name, $port, $workdir, $exe, $svcArgs, $envMap, $health, $timeout, $deps) {
    return [pscustomobject]@{
        Key = $key; Name = $name; Port = $port
        WorkDir = $workdir; Exe = $exe; Args = $svcArgs
        Env = $envMap; Health = $health; Timeout = $timeout; DependsOn = $deps
    }
}

$services += New-Svc 'backend-8000' 'MainBackend' 8000 (Join-Path $Root 'backend') $uv @('run','--python','3.12','--no-sync','python','-m','uvicorn','app.main:app','--host','0.0.0.0','--port','8000') @{} 'http://127.0.0.1:8000/api/v1/health' 90 @()
$services += New-Svc 'sign-8989' 'SignService' 8989 (Join-Path $Root 'backend\agent-stack\sign-service') $uv @('run','--python','3.12','python','app.py') @{ APP_PORT='8989'; APP_ADDRESS='127.0.0.1'; SIGN_TYPE='javascript'; PYTHONUTF8='1'; PYTHONIOENCODING='utf-8' } 'http://127.0.0.1:8989/signsrv/pong' 60 @()
$services += New-Svc 'download-8205' 'DownloadServer' 8205 (Join-Path $Root 'backend\agent-stack\download-service\DownloadServer') $downloadPython @('app.py') @{} 'http://127.0.0.1:8205/ping' 45 @('sign-8989')

if (-not $SkipCrawler) {
    $services += New-Svc 'crawler-8005' 'CrawlerEngine' 8005 (Join-Path $Root 'backend\agent-stack\crawler-engine') $crawlerPython @('api_server.py') @{ CRAWLER_API_PORT='8005' } 'http://127.0.0.1:8005/openapi.json' 60 @('sign-8989')
}

$services += New-Svc 'agent-8002' 'AgentBackend' 8002 (Join-Path $Root 'backend\agent-stack\ai-agent-service\backend') $uv @('run','--python','3.12','--no-editable','--no-sync','python','-m','uvicorn','api.main:app','--host','0.0.0.0','--port','8002') @{} 'http://127.0.0.1:8002/health' 120 @('download-8205')

if (-not $SkipCookieBridge) {
    $services += New-Svc 'cookie-bridge-8274' 'CookieBridge' 8274 (Join-Path $Root 'backend\agent-stack\cookie-bridge\server') $uv @('run','app.py') @{} 'http://127.0.0.1:8274/ping' 45 @()
}

if (-not $SkipFrontend) {
    $services += New-Svc 'frontend-5173' 'MainFrontend' 5173 (Join-Path $Root 'frontend') $cmdExe @('/c','npm','run','dev','--','--host','localhost','--port','5173') @{ PATH = $nodeDir + ';' + $env:PATH } 'http://localhost:5173/' 90 @()
    $services += New-Svc 'agent-frontend-5374' 'AgentFrontend' 5374 (Join-Path $Root 'backend\agent-stack\ai-agent-service\frontend') $cmdExe @('/c','npm','run','dev') @{ PATH = $nodeDir + ';' + $env:PATH } 'http://localhost:5374/' 90 @()
}

$pids = @{}
if (Test-Path -LiteralPath $PidFile) {
    try {
        $old = Get-Content -LiteralPath $PidFile -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($prop in $old.PSObject.Properties) {
            if (Get-Process -Id ([int]$prop.Value) -ErrorAction SilentlyContinue) { $pids[$prop.Name] = [int]$prop.Value }
        }
    } catch { }
}

Write-Host ''
Write-Host '=============================================' -ForegroundColor Cyan
Write-Host ' AI-Content-Automation START ALL' -ForegroundColor Cyan
Write-Host '=============================================' -ForegroundColor Cyan
Write-Host ''
Write-Host '[Infra check] MySQL 3306 / Redis 6379 / MinIO 9000' -ForegroundColor DarkGray
foreach ($infra in @(@{N='MySQL';P=3306}, @{N='Redis';P=6379}, @{N='MinIO';P=9000})) {
    if (Test-Port $infra.P) { Write-Host ('  [OK]   {0} :{1}' -f $infra.N, $infra.P) -ForegroundColor Green }
    else { Write-Host ('  [WARN] {0} :{1} not listening' -f $infra.N, $infra.P) -ForegroundColor Yellow }
}
Write-Host ''

$results = @()
$failed = @{}

foreach ($svc in $services) {
    Write-Host ('[{0}] port {1}' -f $svc.Name, $svc.Port) -ForegroundColor White

    $blocked = $false
    foreach ($dep in $svc.DependsOn) { if ($failed.ContainsKey($dep)) { $blocked = $true } }
    if ($blocked) {
        Write-Host '  [SKIP] dependency not ready' -ForegroundColor Yellow
        $results += [pscustomobject]@{ Name=$svc.Name; Port=$svc.Port; Status='SKIP'; Log='' }
        $failed[$svc.Key] = $true
        continue
    }

    if (Test-Port $svc.Port) {
        Write-Host '  [OK]   already running, skip' -ForegroundColor Green
        $results += [pscustomobject]@{ Name=$svc.Name; Port=$svc.Port; Status='RUNNING'; Log='' }
        continue
    }

    if (-not (Test-Path -LiteralPath $svc.WorkDir)) {
        Write-Host ('  [FAIL] workdir missing: {0}' -f $svc.WorkDir) -ForegroundColor Red
        $results += [pscustomobject]@{ Name=$svc.Name; Port=$svc.Port; Status='FAIL'; Log='' }
        $failed[$svc.Key] = $true
        continue
    }
    if ([string]::IsNullOrWhiteSpace($svc.Exe) -or -not (Test-Path -LiteralPath $svc.Exe)) {
        Write-Host ('  [FAIL] runtime missing: {0}' -f $svc.Exe) -ForegroundColor Red
        $results += [pscustomobject]@{ Name=$svc.Name; Port=$svc.Port; Status='FAIL'; Log='' }
        $failed[$svc.Key] = $true
        continue
    }

    $outLog = Join-Path $LogDir ($svc.Key + '.out.log')
    $errLog = Join-Path $LogDir ($svc.Key + '.err.log')

    $saved = @{}
    foreach ($k in $svc.Env.Keys) {
        $saved[$k] = [Environment]::GetEnvironmentVariable($k, 'Process')
        [Environment]::SetEnvironmentVariable($k, [string]$svc.Env[$k], 'Process')
    }

    try {
        $proc = Start-Process -FilePath $svc.Exe -ArgumentList $svc.Args -WorkingDirectory $svc.WorkDir -RedirectStandardOutput $outLog -RedirectStandardError $errLog -WindowStyle Hidden -PassThru
        $pids[$svc.Key] = $proc.Id
        Write-Host ('  [..]   starting PID={0}' -f $proc.Id) -ForegroundColor DarkGray
    } catch {
        Write-Host ('  [FAIL] start error: {0}' -f $_.Exception.Message) -ForegroundColor Red
        $results += [pscustomobject]@{ Name=$svc.Name; Port=$svc.Port; Status='FAIL'; Log=$errLog }
        $failed[$svc.Key] = $true
        continue
    } finally {
        foreach ($k in $saved.Keys) { [Environment]::SetEnvironmentVariable($k, $saved[$k], 'Process') }
    }

    if (Wait-Health -Url $svc.Health -Seconds $svc.Timeout) {
        Write-Host '  [OK]   health check passed' -ForegroundColor Green
        $results += [pscustomobject]@{ Name=$svc.Name; Port=$svc.Port; Status='OK'; Log='' }
    } else {
        Write-Host ('  [FAIL] health timeout ({0}s), log: {1}' -f $svc.Timeout, $errLog) -ForegroundColor Red
        $results += [pscustomobject]@{ Name=$svc.Name; Port=$svc.Port; Status='FAIL'; Log=$errLog }
        $failed[$svc.Key] = $true
    }
    Write-Host ''
}

$pids | ConvertTo-Json -Depth 3 | Out-File -LiteralPath $PidFile -Encoding UTF8

Write-Host ''
Write-Host '================ RESULT ================' -ForegroundColor Cyan
foreach ($r in $results) {
    $color = 'Green'
    if ($r.Status -eq 'FAIL') { $color = 'Red' }
    elseif ($r.Status -eq 'SKIP') { $color = 'Yellow' }
    Write-Host ('  {0,-18} :{1,-6} {2}' -f $r.Name, $r.Port, $r.Status) -ForegroundColor $color
}
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'logs: .tmp\runlogs' -ForegroundColor DarkGray
Write-Host 'stop: scripts\stop-all.bat' -ForegroundColor DarkGray
Write-Host ''

if ($failed.Count -gt 0) { exit 1 } else { exit 0 }
