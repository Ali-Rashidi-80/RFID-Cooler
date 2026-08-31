#Requires -Version 5.1
<#
.SYNOPSIS
  Flash all RFID-Cooler firmware .py files to ESP32 via mpremote.

.DESCRIPTION
  One-liner (after pip install mpremote):
    powershell -ExecutionPolicy Bypass -File scripts/flash_device.ps1 -Port COM3

  Or from repo root:
    .\scripts\flash_device.ps1 -Port COM3 -IncludeConfig -ConfigPath config.bench.example.json

.PARAMETER Port
  Serial port (e.g. COM3). Auto-detected if omitted (skips COM1 virtual ports when possible).

.PARAMETER IncludeConfig
  Also upload config JSON to device as :config.json

.PARAMETER ConfigPath
  Local config file to upload (default: config.bench.example.json)

.PARAMETER Reset
  Reset board after upload (default: true)
#>
[CmdletBinding()]
param(
    [string] $Port = "",
    [switch] $IncludeConfig,
    [string] $ConfigPath = "config.bench.example.json",
    [switch] $NoReset
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$FirmwareFiles = @(
    "boot.py", "main.py", "mfrc522.py",
    "wifi_manager.py", "ap_manager.py", "local_http.py", "dns_captive.py",
    "outbox.py", "cloud.py", "ws_client.py",
    "wall_inputs.py", "rf433.py", "ble_control.py", "sms_modem.py",
    "mqtt_client.py", "ota_stub.py"
)

function Ensure-Mpremote {
    $mpy = Get-Command mpremote -ErrorAction SilentlyContinue
    if (-not $mpy) {
        $mpyModule = python -m mpremote --help 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[flash] Installing mpremote..." -ForegroundColor Yellow
            python -m pip install -q mpremote
        }
    }
    python -m mpremote --help | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "mpremote not available. Run: pip install mpremote"
    }
}

function Get-EspPort {
    if ($Port) { return $Port.Trim() }
    Write-Host "[flash] Auto-detecting COM port..." -ForegroundColor Cyan
    $detect = python (Join-Path $Root "scripts\bench_port_util.py") best 2>$null
    if (-not $detect) {
        throw "No USB serial port found. Plug ESP32 and pass -Port COMx"
    }
    Write-Host "[flash] Selected $detect" -ForegroundColor Green
    return $detect.Trim()
}

function Invoke-Mpremote {
    param([string[]] $Args)
    & python -m mpremote @Args
    if ($LASTEXITCODE -ne 0) {
        throw "mpremote failed: mpremote $($Args -join ' ')"
    }
}

Ensure-Mpremote
$com = Get-EspPort
Write-Host "[flash] Target $com — $($FirmwareFiles.Count) files" -ForegroundColor Cyan

foreach ($f in $FirmwareFiles) {
    if (-not (Test-Path $f)) { throw "Missing firmware file: $f" }
    Write-Host "  -> $f"
    Invoke-Mpremote @("connect", $com, "fs", "cp", $f, ":$f")
}

if ($IncludeConfig) {
    if (-not (Test-Path $ConfigPath)) { throw "Config not found: $ConfigPath" }
    Write-Host "  -> $ConfigPath as :config.json"
    Invoke-Mpremote @("connect", $com, "fs", "cp", $ConfigPath, ":config.json")
}

if (-not $NoReset) {
    Write-Host "[flash] Reset..." -ForegroundColor Cyan
    Invoke-Mpremote @("connect", $com, "reset")
}

Write-Host "[flash] Done. Monitor: .\scripts\bench_live.ps1 -Port $com" -ForegroundColor Green
