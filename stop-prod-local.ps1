$ErrorActionPreference = "Continue"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Stopping API/worker python processes..."
Get-CimInstance Win32_Process |
    Where-Object {
        $_.Name -eq "python.exe" -and
        ($_.CommandLine -like "*uvicorn app.main:app*" -or $_.CommandLine -like "*-m app.workers.email_worker*")
    } |
    ForEach-Object {
        try {
            Stop-Process -Id $_.ProcessId -Force
            Write-Host "Stopped PID $($_.ProcessId)"
        } catch {
            Write-Host "Could not stop PID $($_.ProcessId): $($_.Exception.Message)"
        }
    }

Write-Host "Stopping PostgreSQL container..."
Push-Location $repoRoot
docker compose stop db | Out-Null
Pop-Location

Write-Host "StudyOS local production stack stopped."

