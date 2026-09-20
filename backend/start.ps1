# start.ps1 — Single command startup for Autonomous SDR Backend
# Runs: cloudflared tunnel → captures URL → updates .env → starts uvicorn
# Usage: powershell -ExecutionPolicy Bypass -File start.ps1

$ErrorActionPreference = "Stop"
$backendDir = $PSScriptRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Autonomous SDR Backend Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Kill any old processes on port 8000 ───────────────────────────────────
Write-Host "[1/4] Freeing port 8000..." -ForegroundColor Yellow
$pid8000 = (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess | Select-Object -Unique
if ($pid8000) {
    Stop-Process -Id $pid8000 -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
}

# ── 2. Start cloudflared in background, capture URL ──────────────────────────
Write-Host "[2/4] Starting Cloudflare tunnel..." -ForegroundColor Yellow

$cfLog = "$env:TEMP\cloudflared_sdr.log"
if (Test-Path $cfLog) { Remove-Item $cfLog -Force }

$cfPath = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
if (-not (Test-Path $cfPath)) {
    $cfPath = (Get-Command cloudflared -ErrorAction SilentlyContinue).Source
}
if (-not $cfPath) {
    Write-Error "cloudflared not found. Run: winget install Cloudflare.cloudflared"
    exit 1
}

$cfProcess = Start-Process -FilePath $cfPath `
    -ArgumentList "tunnel --url http://127.0.0.1:8000" `
    -RedirectStandardError $cfLog `
    -PassThru -NoNewWindow

# Wait for tunnel URL to appear in log (up to 30s)
$tunnelUrl = $null
$waited = 0
Write-Host "   Waiting for tunnel URL..." -ForegroundColor DarkGray
while (-not $tunnelUrl -and $waited -lt 30) {
    Start-Sleep -Milliseconds 800
    $waited += 0.8
    if (Test-Path $cfLog) {
        $content = Get-Content $cfLog -Raw -ErrorAction SilentlyContinue
        if ($content -match "https://[a-z0-9\-]+\.trycloudflare\.com") {
            $tunnelUrl = $Matches[0]
        }
    }
}

if (-not $tunnelUrl) {
    Write-Error "Cloudflare tunnel failed to start. Check: $cfLog"
    Stop-Process -Id $cfProcess.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

Write-Host "   Tunnel URL: $tunnelUrl" -ForegroundColor Green
$voiceUrl = "$tunnelUrl/api/voice/interactive"

# ── 3. Patch TWILIO_VOICE_URL in .env ────────────────────────────────────────
Write-Host "[3/4] Updating .env TWILIO_VOICE_URL..." -ForegroundColor Yellow
$envFile = Join-Path $backendDir ".env"
$envContent = Get-Content $envFile -Raw
# Replace existing TWILIO_VOICE_URL line (any value)
$envContent = $envContent -replace "(?m)^TWILIO_VOICE_URL=.*$", "TWILIO_VOICE_URL=$voiceUrl"
Set-Content -Path $envFile -Value $envContent -NoNewline
Write-Host "   TWILIO_VOICE_URL=$voiceUrl" -ForegroundColor Green

# ── 4. Start uvicorn ─────────────────────────────────────────────────────────
Write-Host "[4/4] Starting uvicorn on port 8000..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Backend running!" -ForegroundColor Green
Write-Host "  Local:    http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "  Public:   $tunnelUrl" -ForegroundColor Green
Write-Host "  Docs:     http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "  TwiML:    $voiceUrl" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $backendDir
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
