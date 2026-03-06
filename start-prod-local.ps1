Param(
    [switch]$ForceRestart,
    [int]$ApiPort = 8010
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $repoRoot "backend"

Write-Host "[1/6] Starting PostgreSQL container..."
Push-Location $repoRoot
docker compose up -d db | Out-Null
Pop-Location

Write-Host "[2/6] Waiting for PostgreSQL healthcheck..."
$maxChecks = 40
$healthy = $false
for ($i = 1; $i -le $maxChecks; $i++) {
    $statusLine = (docker compose -f (Join-Path $repoRoot "docker-compose.yml") ps --format json | ConvertFrom-Json | Where-Object { $_.Service -eq "db" }).Health
    if ($statusLine -eq "healthy") {
        $healthy = $true
        break
    }
    Start-Sleep -Seconds 2
}
if (-not $healthy) {
    throw "PostgreSQL did not become healthy in time."
}

Write-Host "[3/6] Running database migrations..."
Push-Location $backendDir
python -m alembic upgrade head
Pop-Location

$apiLog = Join-Path $backendDir "api.log"
$apiErrLog = Join-Path $backendDir "api.err.log"
$workerLog = Join-Path $backendDir "worker.log"
$workerErrLog = Join-Path $backendDir "worker.err.log"

if ($ForceRestart) {
    Write-Host "[4/6] Stopping existing API/worker processes (if any)..."
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.Name -eq "python.exe" -and
            ($_.CommandLine -like "*uvicorn app.main:app*" -or $_.CommandLine -like "*-m app.workers.email_worker*")
        } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

Write-Host "[5/6] Starting API on port $ApiPort..."
Start-Process -FilePath python `
    -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port $ApiPort" `
    -WorkingDirectory $backendDir `
    -RedirectStandardOutput $apiLog `
    -RedirectStandardError $apiErrLog | Out-Null

Write-Host "[6/6] Starting email worker..."
Start-Process -FilePath python `
    -ArgumentList "-m app.workers.email_worker" `
    -WorkingDirectory $backendDir `
    -RedirectStandardOutput $workerLog `
    -RedirectStandardError $workerErrLog | Out-Null

Write-Host ""
Write-Host "StudyOS local production stack started."
Write-Host "API: http://127.0.0.1:$ApiPort/health"
Write-Host "Logs:"
Write-Host "  $apiLog"
Write-Host "  $apiErrLog"
Write-Host "  $workerLog"
Write-Host "  $workerErrLog"

