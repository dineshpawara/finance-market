# PowerShell Script to run FastAPI Backend from finance folder
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "Starting FastAPI Indian Stock Market Backend Server" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $scriptDir "Scripts\python.exe"

if (Test-Path $pythonExe) {
    Set-Location $scriptDir
    & $pythonExe main.py
} else {
    Write-Error "Python executable not found at $pythonExe"
}
